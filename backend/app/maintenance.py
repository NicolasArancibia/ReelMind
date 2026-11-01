"""Explicit library backup and isolated restore drill. Never overwrites a database."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import socket
import subprocess
from uuid import uuid4

import psycopg
from psycopg import sql
from sqlalchemy import create_engine,text

from app.config import get_settings
from app.db import get_engine
from app.processing import ManualEngine


def digest(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def contained(root,relative):
    root=root.resolve(); path=(root/relative).resolve()
    if not relative or Path(relative).is_absolute() or not path.is_relative_to(root) or path==root:
        raise ValueError('Ruta fuera del almacén.')
    return path


def external(path):
    path=path.resolve()
    forbidden=[Path(__file__).resolve().parents[2]]
    forbidden.extend(Path(os.environ[k]).resolve() for k in ('OneDrive','OneDriveConsumer','OneDriveCommercial') if os.environ.get(k))
    if any(path==root or path.is_relative_to(root) for root in forbidden):
        raise ValueError('El destino debe quedar fuera del proyecto y OneDrive.')
    return path


def fingerprint(connection):
    tables=connection.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")).scalars().all()
    result={}
    for table in tables:
        # Identifiers come exclusively from PostgreSQL's catalog and are quoted.
        name=connection.dialect.identifier_preparer.quote(table)
        rows=connection.execute(text(f'SELECT row_to_json(t)::text FROM public.{name} AS t')).scalars().all()
        canonical=sorted(json.dumps(json.loads(r),sort_keys=True,separators=(',',':'),ensure_ascii=False) for r in rows)
        result[table]={'count':len(rows),'sha256':hashlib.sha256('\n'.join(canonical).encode()).hexdigest()}
    return result


def pg_tool(name,args):
    settings=get_settings()
    binary=Path(os.environ['ProgramFiles'])/'PostgreSQL'/'18'/'bin'/f'{name}.exe'
    command=[str(binary),'-h',settings.pg_host,'-p',str(settings.pg_port),'-U',settings.pg_user,'-w',*args]
    # No raw tool errors: they can contain imported identifiers or connection details.
    env={k:v for k,v in os.environ.items() if k not in {'REELMIND_ADMIN_PASSWORD','REELMIND_ADMIN_USER','HF_TOKEN','HUGGING_FACE_HUB_TOKEN'}}
    result=subprocess.run(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode: raise RuntimeError(f'{name} falló (código {result.returncode}). Se conserva el intento para revisar.')
    return result.stdout


def ensure_stopped():
    with socket.socket() as probe:
        probe.settimeout(2)
        if probe.connect_ex(('127.0.0.1',8000))==0: raise ValueError('Detén ReelMind antes del mantenimiento.')


def backup():
    ensure_stopped(); settings=get_settings(); root=external(settings.data_root)
    database=get_engine(); lock=ManualEngine(database).acquire()
    if lock is None: raise ValueError('Hay otra tarea pesada activa.')
    bundle=external(root.parent/'backups'/('library-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8]))
    try:
        bundle.mkdir(parents=True,exist_ok=False)
        with database.connect().execution_options(isolation_level='REPEATABLE READ') as connection:
            connection.execute(text('SET TRANSACTION READ ONLY'))
            if connection.scalar(text('SELECT state FROM engine_state WHERE id=1'))!='stopped': raise ValueError('El motor debe estar detenido.')
            if connection.scalar(text("SELECT count(*) FROM retrieval_tasks WHERE status IN ('running','stop_requested')")): raise ValueError('Hay consultas sin cerrar.')
            snapshot=connection.scalar(text('SELECT pg_export_snapshot()'))
            expected=fingerprint(connection)
            files=[dict(row) for row in connection.execute(text('SELECT local_path,checksum,size_bytes FROM media_files ORDER BY local_path')).mappings()]
            pg_tool('pg_dump',['-d',settings.pg_database,'-Fc','--no-owner','--no-privileges','--snapshot',snapshot,'-f',str(bundle/'database.dump')])
            for row in files:
                source=contained(root,row['local_path']); target=contained(bundle/'data',row['local_path'])
                validate_media_path(row)
                if source.stat().st_size!=row['size_bytes'] or digest(source)!=row['checksum']: raise ValueError('Medio ausente o corrupto; copia incompleta.')
                target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(source,target)
                if digest(target)!=row['checksum']: raise ValueError('La copia del medio no coincide.')
            manifest={'format':1,'created_at':datetime.now(timezone.utc).isoformat(),'schema':connection.scalar(text('SELECT version_num FROM alembic_version')),
                'database_sha256':digest(bundle/'database.dump'),'tables':expected,'files':files}
            (bundle/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
        print(json.dumps({'backup':str(bundle),'files':len(files),'tables':len(expected)},ensure_ascii=False))
        return bundle
    finally: ManualEngine.release(lock); database.dispose()


def validate_bundle(bundle):
    bundle=external(bundle)
    manifest=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('format')!=1 or manifest.get('schema')!='0008_graph': raise ValueError('Formato/esquema de copia incompatible.')
    if digest(bundle/'database.dump')!=manifest['database_sha256']: raise ValueError('El respaldo SQL no coincide con el manifiesto.')
    if manifest.get('tables',{}).get('media_files',{}).get('count')!=len(manifest['files']):
        raise ValueError('El manifiesto no enumera todos los medios de la base.')
    seen=set()
    for row in manifest['files']:
        relative=row['local_path']
        validate_media_path(row)
        if relative in seen: raise ValueError('Ruta de medio repetida.')
        seen.add(relative); path=contained(bundle/'data',relative)
        if path.stat().st_size!=row['size_bytes'] or digest(path)!=row['checksum']: raise ValueError('Medio de respaldo ausente o corrupto.')
    return bundle,manifest


def validate_media_path(row):
    checksum=row['checksum']
    if not isinstance(checksum,str) or not re.fullmatch('[0-9a-f]{64}',checksum) or row['local_path']!=f'media/{checksum[:2]}/{checksum}':
        raise ValueError('Ruta de medio no válida.')


def restore_verify(bundle):
    ensure_stopped(); bundle,manifest=validate_bundle(bundle); settings=get_settings()
    # Fixed generated namespace: no argument can target the live database or an existing one.
    suffix=uuid4().hex; name='reelmind_restore_'+suffix
    destination=external(settings.data_root.parent/'recovery'/suffix/'data')
    destination.mkdir(parents=True,exist_ok=False)
    with psycopg.connect(host=settings.pg_host,port=settings.pg_port,dbname='postgres',user=os.environ['REELMIND_ADMIN_USER'],
        password=os.environ['REELMIND_ADMIN_PASSWORD'],autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {} OWNER {} TEMPLATE template0').format(sql.Identifier(name),sql.Identifier(settings.pg_user)))
    with psycopg.connect(host=settings.pg_host,port=settings.pg_port,dbname=name,user=os.environ['REELMIND_ADMIN_USER'],
        password=os.environ['REELMIND_ADMIN_PASSWORD'],autocommit=True) as admin:
        admin.execute('CREATE EXTENSION vector WITH SCHEMA public')
    # Extension is prepared by admin; restore application objects using the app role.
    toc=pg_tool('pg_restore',['-l',str(bundle/'database.dump')]).decode('utf-8')
    lines=[line for line in toc.splitlines() if not (' EXTENSION ' in line or ' COMMENT - EXTENSION ' in line)]
    listing=destination.parent/'restore.list'; listing.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    pg_tool('pg_restore',['-d',name,'--no-owner','--no-privileges','--exit-on-error','--single-transaction','-L',str(listing),str(bundle/'database.dump')])
    for row in manifest['files']:
        target=contained(destination,row['local_path']); target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(contained(bundle/'data',row['local_path']),target)
        if digest(target)!=row['checksum']: raise ValueError('Medio restaurado no coincide.')
    restored=create_engine(settings.database_url.set(database=name),hide_parameters=True)
    try:
        with restored.connect() as connection:
            restored_files=[dict(row) for row in connection.execute(text('SELECT local_path,checksum,size_bytes FROM media_files ORDER BY local_path')).mappings()]
            if restored_files!=manifest['files']: raise ValueError('El manifiesto de medios no coincide con la base restaurada.')
            actual=fingerprint(connection)
            if actual!=manifest['tables']: raise ValueError('La base restaurada no coincide con la copia.')
            if connection.scalar(text('SELECT state FROM engine_state WHERE id=1'))!='stopped': raise ValueError('Motor restaurado no detenido.')
    finally: restored.dispose()
    report={'verified':True,'database':name,'data_root':str(destination),'schema':manifest['schema'],
        'tables':len(actual),'files':len(manifest['files']),'model_files_included':False,'secrets_included':False}
    (destination.parent/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False)); return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['backup','restore-verify']);parser.add_argument('--bundle',type=Path)
    args=parser.parse_args()
    try:
        if args.action=='backup': backup()
        elif args.bundle: restore_verify(args.bundle)
        else: parser.error('--bundle es obligatorio para restaurar una copia.')
    except Exception as exc:
        # Avoid secret-bearing exception strings from drivers or subprocesses.
        print(json.dumps({'error_type':type(exc).__name__,'message':str(exc) if isinstance(exc,ValueError) else 'Mantenimiento incompleto. Se conserva el intento; consulta operación local.'},ensure_ascii=False))
        raise SystemExit(1) from None

if __name__=='__main__': main()
