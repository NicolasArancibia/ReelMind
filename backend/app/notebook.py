"""Personal knowledge, with immutable note revisions and exact quoted evidence."""
import json
from uuid import UUID,uuid4
from fastapi import APIRouter,Depends,HTTPException,Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from pydantic import BaseModel,Field
from sqlalchemy import select,func,or_
from sqlalchemy.orm import Session,aliased
from app.db import get_session
from app.models import Source,NoteRevision,ContentChunk,ProjectSource,Transcript,AudiovisualAnalysis,Tag
from app.schemas import SourceMutation

router=APIRouter(prefix='/api')

def latest_notes():
    other=aliased(NoteRevision)
    newest=select(func.max(other.version)).where(other.id==NoteRevision.id).correlate(NoteRevision).scalar_subquery()
    return select(NoteRevision).join(Source,Source.id==NoteRevision.source_id).where(Source.deleted_at.is_(None),NoteRevision.version==newest)

def note_read(row):
    return {k:getattr(row,k) for k in ('id','version','source_id','content','quote_chunk_id','quote_text','start_ms','end_ms','favorite','archived','created_at')}

class NoteInput(BaseModel):
    content:str=Field(min_length=1,max_length=8000)
    quote_chunk_id:UUID|None=None
    start_ms:int|None=Field(default=None,ge=0)
    end_ms:int|None=Field(default=None,ge=1)
    favorite:bool=False
    archived:bool=False
    expected_version:int=Field(default=0,ge=0)

@router.get('/notes')
def notes(source_id:UUID|None=None,project_id:UUID|None=None,tag:UUID|None=None,q:str=Query(default='',max_length=240),
    archived:bool=False,favorite:bool=False,offset:int=Query(default=0,ge=0),limit:int=Query(default=50,ge=1,le=100),session:Session=Depends(get_session)):
    query=latest_notes().where(NoteRevision.archived==archived)
    if source_id:query=query.where(NoteRevision.source_id==source_id)
    if project_id:query=query.where(NoteRevision.source_id.in_(select(ProjectSource.source_id).where(ProjectSource.project_id==project_id)))
    if tag:query=query.where(Source.tags.any(Tag.id==tag))
    if favorite:query=query.where(NoteRevision.favorite.is_(True))
    if q.strip():
        pattern='%'+q.strip().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
        query=query.where(or_(NoteRevision.content.ilike(pattern),NoteRevision.quote_text.ilike(pattern)))
    total=session.scalar(select(func.count()).select_from(query.subquery()))
    return {'items':[note_read(r) for r in session.scalars(query.order_by(NoteRevision.created_at.desc(),NoteRevision.id).offset(offset).limit(limit))], 'total':total,'offset':offset,'limit':limit}

def save_note(source_id,payload,session,note_id=None):
    source=session.get(Source,source_id,with_for_update=True)
    if source is None or source.deleted_at is not None:raise HTTPException(404,'Fuente no disponible.')
    if not payload.content.strip():raise HTTPException(422,'Escribe tu apunte.')
    if (payload.start_ms is None)!=(payload.end_ms is None) or (payload.end_ms is not None and payload.end_ms<=payload.start_ms):raise HTTPException(422,'Revisa el intervalo de tiempo.')
    if payload.end_ms is not None and len(source.assets)==1:
        duration=session.scalar(select(Transcript.duration_ms).where(Transcript.source_id==source_id,Transcript.asset_id==source.assets[0].id).order_by(Transcript.version.desc()).limit(1))
        if duration is not None and payload.end_ms>duration:raise HTTPException(422,'El intervalo supera la duración registrada del vídeo.')
    previous=session.scalar(select(NoteRevision).where(NoteRevision.id==note_id,NoteRevision.source_id==source_id).order_by(NoteRevision.version.desc()).limit(1)) if note_id else None
    if note_id and previous is None:raise HTTPException(404,'Apunte no encontrado.')
    if payload.expected_version!=(previous.version if previous else 0):raise HTTPException(409,'El apunte cambió. Actualiza antes de editar.')
    quote=None
    if payload.quote_chunk_id:
        quote=session.get(ContentChunk,payload.quote_chunk_id)
        if quote is None or quote.source_id!=source_id:raise HTTPException(422,'La cita no pertenece a esta fuente.')
    row=NoteRevision(id=note_id or uuid4(),version=payload.expected_version+1,source_id=source_id,content=payload.content.strip(),
        quote_chunk_id=payload.quote_chunk_id,quote_text=quote.content if quote else None,start_ms=payload.start_ms,end_ms=payload.end_ms,
        favorite=payload.favorite,archived=payload.archived)
    session.add(row);session.commit();session.refresh(row);return note_read(row)

@router.post('/sources/{source_id}/notes',status_code=201)
def create_note(source_id:UUID,payload:NoteInput,session:Session=Depends(get_session)):
    return save_note(source_id,payload,session)

@router.put('/sources/{source_id}/notes/{note_id}')
def revise_note(source_id:UUID,note_id:UUID,payload:NoteInput,session:Session=Depends(get_session)):
    return save_note(source_id,payload,session,note_id)

@router.get('/sources/{source_id}/notes/{note_id}/history')
def note_history(source_id:UUID,note_id:UUID,session:Session=Depends(get_session)):
    source=session.get(Source,source_id)
    if source is None or source.deleted_at is not None:raise HTTPException(404,'Fuente no disponible.')
    return [note_read(r) for r in session.scalars(select(NoteRevision).where(NoteRevision.id==note_id,NoteRevision.source_id==source_id).order_by(NoteRevision.version))]

class SourceDetails(SourceMutation):
    favorite:bool=False
    summary:str|None=Field(default=None,max_length=4000)

@router.put('/sources/{source_id}/details')
def details(source_id:UUID,payload:SourceDetails,session:Session=Depends(get_session)):
    row=session.get(Source,source_id,with_for_update=True)
    if row is None or row.deleted_at is not None:raise HTTPException(404,'Fuente no disponible.')
    from app.main import check_version,commit_source
    check_version(row,payload)
    row.favorite=payload.favorite;row.summary=payload.summary.strip() if payload.summary else None
    commit_source(session,row);return {'favorite':row.favorite,'summary':row.summary,'updated_at':row.updated_at}

@router.get('/sources/{source_id}/export')
def export_source(source_id:UUID,format:str=Query(default='markdown',pattern='^(markdown|json)$'),session:Session=Depends(get_session)):
    source=session.get(Source,source_id)
    if source is None or source.deleted_at is not None:raise HTTPException(404,'Fuente no disponible.')
    entries=[note_read(r) for r in session.scalars(latest_notes().where(NoteRevision.source_id==source_id))]
    title=source.title or (source.assets[0].original_name if source.assets else source.original_url)
    transcripts=[{'id':r.id,'version':r.version,'segments':[{'start_ms':s.start_ms,'end_ms':s.end_ms,'text':s.text} for s in r.segments]} for r in session.scalars(select(Transcript).where(Transcript.source_id==source_id).order_by(Transcript.version))]
    data=jsonable_encoder({'source_id':source.id,'title':title,'original_url':source.original_url,'summary':source.summary,'notes':entries,'transcripts':transcripts})
    if format=='json':body=json.dumps(data,ensure_ascii=False,indent=2);media='application/json';suffix='json'
    else:
        body=f'# {title}\n\nFuente: {source.id}\nEnlace: {source.original_url or "Archivo local"}\n\n{source.summary or ""}\n'
        for n in entries:body+=f'\n## Apunte {n["id"]} · v{n["version"]}{" · Archivado" if n["archived"] else ""}\n\n{n["content"]}\n\nCita original:\n{n["quote_text"] or "Sin cita literal"}\nTiempo (ms): {n["start_ms"]}–{n["end_ms"]}\n'
        media='text/markdown';suffix='md'
    return Response(body,media_type=media,headers={'Content-Disposition':f'attachment; filename="reelmind-{source_id}.{suffix}"'})
