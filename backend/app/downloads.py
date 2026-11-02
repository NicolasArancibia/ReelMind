"""Explicit, cancelable Instagram recovery and idempotent attachment to the original source."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlsplit
from sqlalchemy import select,text,func
from sqlalchemy.orm import Session
from app.config import get_settings
from app.media import storage_path,media_type,publish_file
from app.models import Source,MediaFile,MediaAsset,EngineState
from app.process_guard import ProcessGuard

class DownloadUnavailable(Exception):pass

def supported(url):
    try:
        parsed=urlsplit(url or '')
        return parsed.scheme=='https' and parsed.hostname in {'instagram.com','www.instagram.com','m.instagram.com'} and parsed.port in {None,443} and not parsed.username and not parsed.password and parsed.path.startswith(('/reel/','/reels/','/p/'))
    except ValueError:return False

def recover_video(url,attempt_id,cancelled):
    from app.processing import Cancelled
    if not supported(url):raise DownloadUnavailable('La descarga automática admite reels públicos de Instagram. Adjunta una copia para otros enlaces.')
    work=storage_path(f'work/{attempt_id}/download');work.mkdir(parents=True,exist_ok=False)
    (work.parent/'progress.json').write_text(json.dumps({'stage':'download'}),encoding='utf-8')
    env={k:v for k,v in os.environ.items() if not k.startswith(('PG','REELMIND_ADMIN','HF_','HUGGING_FACE','OLLAMA_')) and k.upper() not in {'HTTP_PROXY','HTTPS_PROXY','ALL_PROXY'}}
    process=subprocess.Popen([sys.executable,'-m','app.download_task',str(work),str(get_settings().max_upload_bytes)],
        stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env,
        cwd=Path(__file__).resolve().parents[1],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    try:
        with ProcessGuard(process):
            process.stdin.write(('1'+url+'\n').encode());process.stdin.flush();process.stdin.close()
            started=time.monotonic()
            while process.poll() is None:
                if cancelled():raise Cancelled()
                if time.monotonic()-started>180:raise DownloadUnavailable('La descarga agotó su tiempo límite. Reintenta o adjunta una copia local.')
                time.sleep(.2)
            if cancelled():raise Cancelled()
            if process.returncode:raise DownloadUnavailable('La descarga se interrumpió. Reintenta o adjunta una copia local.')
            info=json.loads((work/'download-result.json').read_text(encoding='utf-8'))
            if info.get('file')!='video.mp4':raise DownloadUnavailable('Instagram no permitió recuperar el vídeo público: puede exigir acceso, limitar solicitudes o no estar disponible. Reintenta más tarde o adjunta una copia local.')
            return work/'video.mp4',{'download_provider':info['provider'],'download_version':info['version']}
    finally:
        if process.poll() is None:process.kill()
        process.wait()

def attach_video(connection,source_id,path,cancelled):
    from app.processing import Cancelled
    limit=get_settings().max_upload_bytes
    if not path.is_file() or not 0<path.stat().st_size<=limit:raise DownloadUnavailable('La descarga no tiene un tamaño válido.')
    with path.open('rb') as stream:
        mime=media_type('reel.mp4',stream.read(32));stream.seek(0);checksum=hashlib.file_digest(stream,'sha256').hexdigest()
    relative=f'media/{checksum[:2]}/{checksum}'
    if cancelled():raise Cancelled()
    with Session(connection,expire_on_commit=False) as session:
        session.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':int.from_bytes(bytes.fromhex(checksum[:16]),'big',signed=True)})
        state=session.get(EngineState,1,with_for_update=True)
        source=session.get(Source,source_id,with_for_update=True)
        if state.state=='stop_requested':raise Cancelled()
        if source is None or source.deleted_at is not None or source.job.status!='running':raise DownloadUnavailable('La fuente cambió. Actualiza antes de reintentar.')
        if source.assets:return source.assets[0]
        physical=session.scalar(select(MediaFile).where(MediaFile.checksum==checksum))
        # Keep promoted bytes after an uncertain commit, just as manual imports do.
        publish_file(path,storage_path(relative))
        if physical is None:
            physical=MediaFile(checksum=checksum,local_path=relative,mime_type=mime,size_bytes=storage_path(relative).stat().st_size);session.add(physical);session.flush()
        asset=MediaAsset(source_id=source_id,file=physical,original_name=f'reel-{source_id}.mp4');session.add(asset)
        source.updated_at=func.clock_timestamp();session.commit();return asset
