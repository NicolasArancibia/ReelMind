"""Explicit, cancellable local retrieval. The shared lock covers inference and commit."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from uuid import UUID,uuid4

from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy import select,update,func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.embeddings import manifest,ready,vectors,MODEL,DIMENSIONS,CHUNK_CHARS
from app.media import storage_path
from app.models import ContentChunk,ChunkEmbedding,EmbeddingProfile,RetrievalTask,ChatSession,Project,ProjectSource,Source
from app.process_guard import ProcessGuard
from app.processing import ManualEngine,Cancelled
from app.retrieval_data import snapshots,live_chunks,ranked,hydrate

router=APIRouter(prefix='/api/retrieval')
ACTIVE=('running','stop_requested')

def local_help(query):
    normalized=query.lower().strip(' ¿?¡!.,')
    if normalized in {'hola','buenas','ayuda','qué puedes hacer','que puedes hacer'}:
        return 'Hola. Puedo ayudarte a encontrar, resumir y comparar lo que contienen tus vídeos y apuntes, con citas. Añade fuentes en Biblioteca e inicia su análisis manualmente; actualiza el índice en Biblioteca disponible. Puedes guardar destacados y verlos en Mis ideas, o elegir un proyecto para limitar la conversación. Esta ayuda no consulta tus vídeos ni inicia modelos.'
    return None


def run_inference(payload,cancelled):
    work=storage_path(f'work/{uuid4()}'); work.mkdir(parents=True,exist_ok=False)
    (work/'input.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
    env={k:v for k,v in os.environ.items() if k not in {'PGPASSWORD','HF_TOKEN','HUGGING_FACE_HUB_TOKEN'}}
    process=None
    try:
        process=subprocess.Popen([sys.executable,'-m','app.retrieval_task',str(get_settings().data_root),str(work)],
            stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env,
            cwd=Path(__file__).resolve().parents[1],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        with ProcessGuard(process):
            process.stdin.write(b'1'); process.stdin.flush(); process.stdin.close()
            started=time.monotonic()
            while process.poll() is None:
                if cancelled(): raise Cancelled()
                if time.monotonic()-started>get_settings().audio_timeout_seconds: raise TimeoutError()
                time.sleep(.2)
            if cancelled(): raise Cancelled()
            if process.returncode: raise RuntimeError('inference')
            result=json.loads((work/'result.json').read_text(encoding='utf-8'))
            if 'error' in result: raise RuntimeError('inference')
            return result
    finally:
        if process:
            if process.poll() is None: process.kill()
            process.wait()
        for name in ('input.json','result.json'): (work/name).unlink(missing_ok=True)
        work.rmdir()


def missing_chunks(session,profile):
    rows=snapshots(session)
    indexed=set(session.scalars(select(ContentChunk.origin_key).join(ChunkEmbedding)
        .where(ChunkEmbedding.profile_id==profile)).all())
    return [row for row in rows if row['origin_key'] not in indexed],len(rows)


def save_index(session,prepared,rows,values):
    values=vectors(values,len(rows))
    profile=session.get(EmbeddingProfile,prepared['profile_id'])
    if profile is None:
        session.add(EmbeddingProfile(id=prepared['profile_id'],model=MODEL,digest=prepared['embedding']['digest'],dimensions=DIMENSIONS,
            configuration={'chunk_chars':CHUNK_CHARS,'pipeline':1,'normalize':'l2'})); session.flush()
    for row,embedding in zip(rows,values):
        chunk=session.scalar(select(ContentChunk).where(ContentChunk.origin_key==row['origin_key']))
        if chunk is None:
            data=dict(row)
            for key in ('source_id','analysis_id','transcript_id','note_id'):
                if key not in data: continue
                if data[key]: data[key]=UUID(data[key])
            chunk=ContentChunk(**data); session.add(chunk); session.flush()
        elif chunk.content_sha256!=row['content_sha256']:
            raise ValueError('La evidencia cambió sin nueva versión.')
        if session.get(ChunkEmbedding,(chunk.id,profile.id if profile else prepared['profile_id'])) is None:
            session.add(ChunkEmbedding(chunk_id=chunk.id,profile_id=prepared['profile_id'],embedding=embedding))


class RetrievalEngine:
    def __init__(self,database,runner=run_inference):
        self.database,self.runner=database,runner
        self.lock=ManualEngine(database); self.shutdown=threading.Event(); self.thread=None

    def recover(self):
        connection=self.lock.acquire()
        if connection is None: return False
        try:
            with Session(connection) as session:
                session.execute(update(RetrievalTask).where(RetrievalTask.status.in_(ACTIVE)).values(status='stopped',
                    error_message='Consulta interrumpida. Puedes iniciarla de nuevo.',finished_at=func.clock_timestamp()))
                session.commit()
            return True
        finally: self.lock.release(connection)

    def start(self,action,query='',session_id=None,project_id=None,source_ids=None,answer_mode='grounded'):
        help_text=local_help(query) if action=='chat' else None
        if help_text:
            with Session(self.database) as session:
                if project_id:
                    project=session.get(Project,project_id)
                    if project is None or project.archived_at is not None:raise HTTPException(409,'Proyecto no disponible.')
                if session_id:
                    chat=session.get(ChatSession,session_id,with_for_update=True)
                    if chat is None or chat.archived_at is not None:raise HTTPException(404,'Conversación no disponible.')
                    if chat.project_id!=project_id:raise HTTPException(409,'Crea otra conversación para cambiar de proyecto.')
                else:
                    chat=ChatSession(title=query[:120],project_id=project_id);session.add(chat);session.flush();session_id=chat.id
                task=RetrievalTask(action='chat',status='completed',query=query,session_id=session_id,profile_id='local-help',finished_at=func.clock_timestamp(),
                    result={'help':help_text,'scope':{'project_id':str(project_id) if project_id else None,'source_ids':[str(i) for i in (source_ids or [])],'answer_mode':answer_mode}})
                session.add(task);session.flush();task_id=task.id;session.commit();return task_id
        if not ready(get_settings().data_root): raise HTTPException(409,'Falta preparar los modelos de búsqueda locales.')
        prepared=manifest(get_settings().data_root)
        connection=self.lock.acquire()
        if connection is None: raise HTTPException(409,'Hay otra tarea pesada activa. Espera o detén el motor.')
        try:
            with Session(connection) as session:
                # A previous interrupted API never causes automatic inference.
                session.execute(update(RetrievalTask).where(RetrievalTask.status.in_(ACTIVE)).values(status='stopped',
                    error_message='Ejecución anterior interrumpida.',finished_at=func.clock_timestamp()))
                if action!='index':
                    missing,total=missing_chunks(session,prepared['profile_id'])
                    if not total: raise HTTPException(409,'No hay evidencias analizables. Analiza primero un vídeo.')
                    if missing: raise HTTPException(409,'El índice está pendiente. Pulsa Actualizar índice antes de consultar.')
                source_ids=source_ids or []
                if project_id:
                    project=session.get(Project,project_id)
                    if project is None or project.archived_at is not None: raise HTTPException(409,'Proyecto no disponible.')
                for source_id in source_ids:
                    source=session.get(Source,source_id)
                    if source is None or source.deleted_at is not None: raise HTTPException(409,'Fuente no disponible.')
                    if project_id and session.get(ProjectSource,(project_id,source_id)) is None: raise HTTPException(409,'Fuente fuera del proyecto.')
                if action=='chat':
                    if session_id:
                        chat=session.get(ChatSession,session_id)
                        if chat is None or chat.archived_at is not None:raise HTTPException(404,'Conversación no disponible.')
                        if project_id!=chat.project_id:raise HTTPException(409,'Crea otra conversación para cambiar de proyecto.')
                    if session_id is None:
                        chat=ChatSession(title=query[:120],project_id=project_id); session.add(chat); session.flush(); session_id=chat.id
                task=RetrievalTask(action=action,status='running',query=query,session_id=session_id,profile_id=prepared['profile_id'],result={'scope':{'project_id':str(project_id) if project_id else None,'source_ids':[str(i) for i in source_ids],'answer_mode':answer_mode}})
                session.add(task); session.flush(); task_id=task.id; session.commit()
            self.shutdown.clear()
            self.thread=threading.Thread(target=self.loop,args=(connection,task_id,prepared),daemon=True)
            self.thread.start()
            return task_id
        except BaseException:
            self.lock.release(connection); raise

    def loop(self,connection,task_id,prepared):
        def cancelled():
            if self.shutdown.is_set(): return True
            with Session(connection) as session: return session.get(RetrievalTask,task_id).status=='stop_requested'
        try:
            result={}; scope={}; state='completed'; error=None
            try:
                with Session(connection) as session:
                    task=session.get(RetrievalTask,task_id); action,query=task.action,task.query
                    scope=task.result.get('scope',{})
                    if action=='index': rows,total=missing_chunks(session,prepared['profile_id'])
                    else:
                        # Follow-up retrieval carries bounded previous questions, never model prose.
                        previous=session.scalars(select(RetrievalTask.query).where(RetrievalTask.session_id==task.session_id,
                            RetrievalTask.id!=task_id,RetrievalTask.status=='completed',RetrievalTask.action=='chat')
                            .order_by(RetrievalTask.created_at.desc()).limit(3)).all() if task.session_id else []
                        context='\n'.join([*reversed(previous),query])
                if action=='index':
                    # Checkpoint complete batches; opening/restarting never resumes them.
                    added=0
                    for offset in range(0,len(rows),128):
                        batch=rows[offset:offset+128]
                        values=self.runner({'action':'embed','texts':[r['content'] for r in batch]},cancelled)['vectors']
                        if cancelled(): raise Cancelled()
                        with Session(connection) as session:
                            task=session.get(RetrievalTask,task_id,with_for_update=True)
                            if task.status=='stop_requested': raise Cancelled()
                            save_index(session,prepared,batch,values)
                            added+=len(batch);task.result={'added':added,'total':total};session.commit()
                    rows=[]; values=[]
                    result={'added':len(rows),'total':total}
                    result['added']=added
                else:
                    from app.retrieval_data import overview_requested,sampled_overview
                    overview=action=='chat' and len(scope.get('source_ids',[]))==1 and overview_requested(query)
                    vector=None if overview else vectors(self.runner({'action':'embed','texts':[context]},cancelled)['vectors'],1)[0]
                    coverage=None
                    with Session(connection) as session:
                        if overview:
                            hits,total=sampled_overview(session,prepared['profile_id'],scope['source_ids'],scope.get('project_id'))
                            coverage={'method':'temporal_sample','sampled':len(hits),'available':total}
                        else:hits=ranked(session,prepared['profile_id'],vector,limit=6,project_id=scope.get('project_id'),source_ids=scope.get('source_ids'))
                        candidates=hydrate(session,hits)
                    result={'hits':hits,'selected':[],'threshold':None if overview else .5,'scope':scope,'coverage':coverage}
                    if action=='chat' and candidates:
                        response=self.runner({'action':'select','query':query,'context':'\n'.join(reversed(previous)),'hits':candidates,'mode':scope.get('answer_mode','grounded')},cancelled)
                        selected=response['selected']
                        result['claims']=response.get('claims',[])
                        result['fallback']=response.get('fallback',False)
                        allowed={h['chunk_id'] for h in candidates}
                        if not isinstance(selected,list) or len(selected)>4 or any(not isinstance(i,str) or i not in allowed for i in selected):
                            raise ValueError('Cita no válida.')
                        result['selected']=list(dict.fromkeys(selected))
                        result['text_model']=prepared['text']
            except Cancelled: state,error='stopped','Detenido por solicitud. Se conservan los lotes completos del índice.'
            except Exception: state,error='failed','No se pudo completar. Comprueba modelos locales, espacio y tiempo límite; puedes reintentar.'
            with Session(connection) as session:
                task=session.get(RetrievalTask,task_id,with_for_update=True)
                if task.status=='stop_requested' or self.shutdown.is_set(): state,error='stopped','Detenido por solicitud. Se conservan los lotes completos del índice.'
                if state=='completed' and action=='index':
                    try:
                        with session.begin_nested(): save_index(session,prepared,rows,values)
                    except Exception: state,error='failed','No se pudo guardar el índice; se conserva la versión anterior.'
                task.status=state; task.error_message=error; task.result=result if state=='completed' else {'scope':scope}
                task.finished_at=func.clock_timestamp(); session.commit()
        finally: self.lock.release(connection)

    def close(self):
        self.shutdown.set()
        if self.thread: self.thread.join(timeout=15)


class StartRequest(BaseModel):
    action: str=Field(pattern='^(index|search|chat)$')
    query: str=Field(default='',max_length=800)
    session_id: UUID | None=None
    answer_mode: str=Field(default='grounded',pattern='^(grounded|extractive)$')
    project_id: UUID | None=None
    source_ids: list[UUID]=Field(default_factory=list,max_length=100)


def task_read(session,task):
    hits=hydrate(session,task.result.get('hits',[]),historical=task.action=='chat')
    selected=set(task.result.get('selected',[]))
    return {'id':task.id,'action':task.action,'query':task.query,'session_id':task.session_id,'status':task.status,
        'created_at':task.created_at,'error_message':task.error_message,'profile_id':task.profile_id,
        'hits':hits,'selected':[h for h in hits if h['chunk_id'] in selected],
        'claims':[claim for claim in task.result.get('claims',[]) if claim.get('chunk_id') in {h['chunk_id'] for h in hits}], 'fallback':task.result.get('fallback',False),'help':task.result.get('help'),
        'added':task.result.get('added'),'total':task.result.get('total'),'scope':task.result.get('scope',{}),'coverage':task.result.get('coverage')}


@router.get('/status')
def status(session:Session=Depends(get_session)):
    prepared=ready(get_settings().data_root)
    missing,total=([],0)
    if prepared: missing,total=missing_chunks(session,manifest(get_settings().data_root)['profile_id'])
    current=session.scalar(select(RetrievalTask).where(RetrievalTask.status.in_(ACTIVE)).order_by(RetrievalTask.created_at.desc()).limit(1))
    return {'ready':prepared,'total':total,'missing':len(missing),'current':task_read(session,current) if current else None}


@router.post('/tasks',status_code=202)
def start(payload:StartRequest,request:Request):
    if payload.action!='index' and not payload.query.strip(): raise HTTPException(422,'Escribe una consulta.')
    task_id=request.app.state.retrieval.start(payload.action,payload.query.strip(),payload.session_id if payload.action=='chat' else None,payload.project_id,payload.source_ids,payload.answer_mode)
    return {'id':task_id}


@router.get('/tasks/{task_id}')
def task(task_id:UUID,session:Session=Depends(get_session)):
    row=session.get(RetrievalTask,task_id)
    if row is None: raise HTTPException(404,'Consulta no encontrada.')
    return task_read(session,row)


@router.post('/tasks/{task_id}/stop')
def stop(task_id:UUID,session:Session=Depends(get_session)):
    row=session.get(RetrievalTask,task_id,with_for_update=True)
    if row is None: raise HTTPException(404,'Consulta no encontrada.')
    if row.status=='running': row.status='stop_requested'; session.commit()
    return task_read(session,row)


@router.get('/sessions')
def sessions(archived:bool=False,q:str='',offset:int=0,limit:int=50,session:Session=Depends(get_session)):
    if offset<0 or limit<1 or limit>100 or len(q)>240:raise HTTPException(422,'Revisa búsqueda y página.')
    condition=ChatSession.archived_at.is_not(None) if archived else ChatSession.archived_at.is_(None)
    query=select(ChatSession).where(condition)
    if q.strip():query=query.where(ChatSession.title.ilike('%'+q.strip().replace('%','\\%').replace('_','\\_')+'%'))
    return [{'id':row.id,'title':row.title,'project_id':row.project_id,'archived':row.archived_at is not None} for row in session.scalars(query.order_by(ChatSession.created_at.desc(),ChatSession.id).offset(offset).limit(limit))]

class ChatChange(BaseModel):
    title:str=Field(min_length=1,max_length=120)
    archived:bool=False
    expected_title:str
    expected_archived:bool=False

@router.put('/sessions/{session_id}')
def change_session(session_id:UUID,payload:ChatChange,session:Session=Depends(get_session)):
    row=session.get(ChatSession,session_id,with_for_update=True)
    if row is None:raise HTTPException(404,'Conversación no encontrada.')
    if not payload.title.strip():raise HTTPException(422,'Escribe un título.')
    if row.title!=payload.expected_title or (row.archived_at is not None)!=payload.expected_archived:raise HTTPException(409,'La conversación cambió. Actualiza antes de editar.')
    row.title=payload.title.strip();row.archived_at=func.clock_timestamp() if payload.archived else None
    session.commit();return {'id':row.id,'title':row.title,'project_id':row.project_id,'archived':row.archived_at is not None}

@router.get('/sessions/{session_id}/export')
def export_session(session_id:UUID,session:Session=Depends(get_session)):
    from fastapi.responses import Response
    row=session.get(ChatSession,session_id)
    if row is None:raise HTTPException(404,'Conversación no encontrada.')
    body='# '+row.title+'\n'
    for task in session.scalars(select(RetrievalTask).where(RetrievalTask.session_id==session_id).order_by(RetrievalTask.created_at)):
        rendered=task_read(session,task);body+='\n## Tú\n'+task.query+'\n\n## ReelMind\n'
        if rendered.get('coverage'):
            coverage=rendered['coverage'];body+=f"Muestra temporal: {coverage['sampled']} de {coverage['available']} fragmentos indexados. La respuesta puede usar solo parte; no representa el vídeo completo.\n\n"
        for claim in rendered.get('claims',[]):body+=claim['text']+'\n'
        for hit in rendered['selected']:body+=hit['content']+f"\nFuente: {hit['source_id']} · {hit['origin']} · ms {hit['time_ms'] if hit['time_ms'] is not None else hit['start_ms']}\n"
        if rendered.get('help'):body+=rendered['help']+'\n'
        elif not rendered['selected']:body+='Sin evidencia suficiente o consulta no completada.\n'
    return Response(body,media_type='text/markdown',headers={'Content-Disposition':f'attachment; filename="chat-{session_id}.md"'})

@router.get('/sessions/{session_id}')
def history(session_id:UUID,session:Session=Depends(get_session)):
    if session.get(ChatSession,session_id) is None: raise HTTPException(404,'Conversación no encontrada.')
    return [task_read(session,row) for row in session.scalars(select(RetrievalTask).where(RetrievalTask.session_id==session_id)
        .order_by(RetrievalTask.created_at,RetrievalTask.id))]
