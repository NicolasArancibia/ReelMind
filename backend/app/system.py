import json
from pathlib import Path
import shutil
from typing import Literal
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import Response
from pydantic import BaseModel,Field
from sqlalchemy import select,func,text
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import get_session
from app.models import Source,Tag,Category,MediaFile,EngineState,RetrievalTask,ProcessingAttempt
from app.processing import HEAVY_LOCK,ready as audio_ready
from app.embeddings import ready as search_ready
from app.local_ai import prepared
from app.schemas import OrganizationUpdate
from app.organization_lock import lock_organization

router=APIRouter(prefix='/api/system')

@router.get('/status')
def status(session:Session=Depends(get_session)):
    root=get_settings().data_root
    size=session.scalar(select(func.coalesce(func.sum(MediaFile.size_bytes),0)))
    files=session.scalar(select(func.count()).select_from(MediaFile))
    task=session.scalar(select(RetrievalTask).where(RetrievalTask.status.in_(['running','stop_requested'])).order_by(RetrievalTask.created_at.desc()).limit(1))
    heavy=session.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE locktype='advisory' AND classid=:high AND objid=:low AND granted AND database=(SELECT oid FROM pg_database WHERE datname=current_database()))"),{'high':HEAVY_LOCK>>32,'low':HEAVY_LOCK&0xffffffff})
    attempt=session.scalar(select(ProcessingAttempt).where(ProcessingAttempt.status=='running').order_by(ProcessingAttempt.started_at.desc()).limit(1))
    stage=None
    if attempt:
        from app.media import storage_path
        import re
        try:
            value=json.loads(storage_path(f'work/{attempt.id}/progress.json').read_text(encoding='utf-8'))['stage']
            if value in {'audio','synthesis','references'} or re.fullmatch(r'vision-[0-7]',value):stage=value
        except (OSError,ValueError,KeyError,TypeError):pass
    backups=root.parent/'backups'
    copies=sorted([p for p in backups.glob('library-*') if p.is_dir() and (p/'manifest.json').is_file()],key=lambda p:p.stat().st_mtime,reverse=True)[:10] if backups.exists() else []
    return {'data_root':str(root),'media_bytes':int(size),'media_files':files,'disk_free_bytes':shutil.disk_usage(root if root.exists() else root.parent).free,
        'audio_ready':audio_ready(),'audiovisual_ready':prepared(root),'search_ready':search_ready(root),
        'engine':session.get(EngineState,1).state,'processing_stage':stage,'heavy_busy':bool(heavy),'task':{'id':task.id,'action':task.action,'status':task.status,'added':task.result.get('added'),'total':task.result.get('total')} if task else None,
        'backups':[{'name':p.name,'path':str(p),'created_at_unix':p.stat().st_mtime} for p in copies]}

class LabelChange(BaseModel):
    name:str=Field(min_length=1,max_length=60)
    expected_name:str

@router.put('/taxonomy/{kind}/{label_id}')
def rename_label(kind:Literal['tags','categories'],label_id:UUID,payload:LabelChange,session:Session=Depends(get_session)):
    try:name=OrganizationUpdate.clean_names([payload.name])[0]
    except (ValueError,IndexError):raise HTTPException(422,'Revisa el nombre.') from None
    lock_organization(session)
    model=Tag if kind=='tags' else Category
    sources=session.scalars(select(Source).where(getattr(Source,kind).any(model.id==label_id)).order_by(Source.id).with_for_update()).all()
    row=session.get(model,label_id,with_for_update=True)
    if row is None:raise HTTPException(404,'Etiqueta o categoría no encontrada.')
    if row.name!=payload.expected_name:raise HTTPException(409,'El nombre cambió. Actualiza antes de editar.')
    other=session.scalar(select(model).where(model.normalized_name==name.casefold(),model.id!=label_id))
    if other:raise HTTPException(409,'Ya existe ese nombre. No se fusionaron datos automáticamente.')
    row.name=name;row.normalized_name=name.casefold()
    for source in sources:source.updated_at=func.clock_timestamp()
    session.commit();return {'id':row.id,'name':row.name,'sources_updated':len(sources)}

@router.get('/export')
def export_library(session:Session=Depends(get_session)):
    session.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
    schema=session.scalar(text('SELECT current_schema()'))
    tables=session.execute(text("SELECT tablename FROM pg_tables WHERE schemaname=:schema ORDER BY tablename"),{'schema':schema}).scalars().all()
    data={}
    for table in tables:
        if table in {'chunk_embeddings','embedding_profiles','engine_state'}:continue
        quoted=session.bind.dialect.identifier_preparer.quote(table)
        namespace=session.bind.dialect.identifier_preparer.quote(schema)
        data[table]=[json.loads(row) for row in session.execute(text(f'SELECT row_to_json(t)::text FROM {namespace}.{quoted} AS t')).scalars()]
    return Response(json.dumps({'format':'reelmind-readable-1','tables':data},ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':'attachment; filename="reelmind-library.json"'})
