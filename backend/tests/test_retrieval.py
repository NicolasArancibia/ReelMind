import hashlib
import threading
import time
from uuid import UUID
from types import SimpleNamespace

import pytest
from sqlalchemy import select,func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.embeddings import vectors,profile_id
from app.main import app
from app.models import ContentChunk,ChunkEmbedding,RetrievalTask,Source,Transcript
from app.processing import Cancelled
from app.retrieval import save_index,missing_chunks
from app.retrieval_data import split_text,snapshots,ranked,hydrate
from app.retrieval_task import select_evidence
from test_audio_engine import upload,result,requeue,finish

VECTOR=[1.0]+[0.0]*1023
PROFILE={'profile_id':profile_id('test'),'embedding':{'digest':'test'},'text':{'name':'test','digest':'test'}}


def test_exact_chunk_offsets_and_embedding_validation():
    value='á🙂 texto '*300
    chunks=list(split_text(value))
    assert ''.join(part for _,part in chunks)==value
    assert all(value[offset:offset+len(part)]==part and len(part)<=1200 for offset,part in chunks)
    assert vectors([[2.0]+[0.0]*1023],1)==[VECTOR]
    for rows,count in [([],1),([[0]*1024],1),([[float('nan')]+[0]*1023],1),([[True]+[0]*1023],1),([[1]*8],1)]:
        with pytest.raises(ValueError): vectors(rows,count)
    assert profile_id('a')!=profile_id('b')


@pytest.fixture
def indexed_source(client,monkeypatch):
    monkeypatch.setattr('app.processing.ready',lambda:True)
    processor=app.state.processor; processor.runner=lambda *args:result()
    source=upload(client)
    client.post('/api/processing/start'); finish(processor)
    monkeypatch.setattr('app.retrieval.ready',lambda root:True)
    monkeypatch.setattr('app.retrieval.manifest',lambda root:PROFILE)
    app.state.retrieval.runner=lambda payload,cancelled:{'vectors':[VECTOR for _ in payload.get('texts',[])]} if payload['action']=='embed' else {'selected':[payload['hits'][0]['chunk_id']]}
    return source


def run(client,action,query='',session_id=None):
    response=client.post('/api/retrieval/tasks',json={'action':action,'query':query,'session_id':session_id})
    assert response.status_code==202,response.text
    finish(app.state.retrieval)
    return client.get('/api/retrieval/tasks/'+response.json()['id']).json()


def test_index_search_chat_persisted_citations_and_version_filter(client,indexed_source,database):
    assert client.post('/api/retrieval/tasks',json={'action':'search','query':'texto'}).status_code==409
    first=run(client,'index'); assert first['status']=='completed' and first['added']==1
    assert run(client,'index')['added']==0
    chat=run(client,'chat','¿Qué dice el vídeo?')
    assert chat['status']=='completed' and chat['selected'][0]['content']=='Texto comprobado'
    assert chat['selected'][0]['start_ms']==0 and chat['selected'][0]['origin']['version']==1
    assert client.get('/api/retrieval/sessions/'+chat['session_id']).json()[0]['selected']==chat['selected']
    with Session(database[0]) as session:
        assert ranked(session,'another-profile',VECTOR)==[]
        assert ranked(session,PROFILE['profile_id'],[0.0,1.0]+[0.0]*1022)==[]
    requeue(client,indexed_source); client.post('/api/processing/start'); finish(app.state.processor)
    with Session(database[0]) as session:
        assert ranked(session,PROFILE['profile_id'],VECTOR)==[]
    old=client.get('/api/retrieval/tasks/'+chat['id']).json()
    assert old['selected'][0]['historical'] is True
    assert client.post('/api/retrieval/tasks',json={'action':'search','query':'texto'}).status_code==409
    assert run(client,'index')['added']==1
    assert run(client,'search','texto')['hits'][0]['origin']['version']==2
    source=client.get('/api/sources/'+indexed_source['id']).json()
    client.request('DELETE','/api/sources/'+source['id'],json={'expected_updated_at':source['updated_at']})
    assert client.get('/api/retrieval/tasks/'+chat['id']).json()['selected']==[]
    assert client.get('/api/retrieval/status').json()['total']==0


def test_index_atomicity_constraints_and_profile_dimension(client,indexed_source,database):
    with Session(database[0]) as session:
        rows=snapshots(session)
        assert rows[0]['content_sha256']==hashlib.sha256(rows[0]['content'].encode()).hexdigest()
        with pytest.raises(ValueError): save_index(session,PROFILE,rows,[[1]])
        session.rollback()
        assert session.scalar(select(func.count()).select_from(ContentChunk))==0
        save_index(session,PROFILE,rows,[VECTOR]); session.commit()
        other=Source(source_type='url',platform='other',original_url='https://example.org/other',canonical_url='https://example.org/other')
        session.add(other); session.flush()
        row=dict(rows[0]); row.update(source_id=other.id,transcript_id=UUID(row['transcript_id']),origin_key='invalid')
        session.add(ContentChunk(**row))
        with pytest.raises(IntegrityError): session.commit()
        session.rollback()
        assert session.scalar(select(func.count()).select_from(ContentChunk))==1


def test_cancellation_shared_lock_recovery_and_no_auto_retry(client,indexed_source,database):
    entered=threading.Event()
    def runner(payload,cancelled):
        entered.set()
        while not cancelled(): time.sleep(.01)
        raise Cancelled()
    app.state.retrieval.runner=runner
    response=client.post('/api/retrieval/tasks',json={'action':'index'})
    assert entered.wait(3)
    assert client.post('/api/processing/start').status_code==409
    assert client.post('/api/retrieval/tasks',json={'action':'index'}).status_code==409
    url='/api/retrieval/tasks/'+response.json()['id']
    client.post(url+'/stop'); finish(app.state.retrieval)
    assert client.get(url).json()['status']=='stopped'
    with Session(database[0]) as session:
        assert session.scalar(select(func.count()).select_from(ChunkEmbedding))==0
        interrupted=RetrievalTask(action='index',status='running',profile_id=PROFILE['profile_id'])
        session.add(interrupted); session.commit(); task_id=interrupted.id
    assert app.state.retrieval.recover()
    assert client.get('/api/retrieval/tasks/'+str(task_id)).json()['status']=='stopped'
    assert client.get('/api/retrieval/status').json()['current'] is None


def test_closed_citations_and_insufficient_evidence():
    class Provider:
        def __init__(self,value): self.value=value
        def chat(self,*args,**kwargs): return self.value
    hits=[{'chunk_id':'known','content':'Una cita exacta.'}]
    assert select_evidence(Provider({'selected':[]}), '¿Clima?',hits)==[]
    assert select_evidence(Provider({'selected':['known']}),'¿Qué dice?',hits)==['known']
    with pytest.raises(ValueError): select_evidence(Provider({'selected':['invented']}),'?',hits)


def test_index_excludes_experimental_and_uncertain_visual_evidence():
    clear={'id':'v0','kind':'visual','description':'Texto observado','visible_text':'Una frase', 'time_ms':100,'uncertain':False}
    rows=[SimpleNamespace(id='record',source_id='source',version=2,payload={'provenance':{'pipeline_version':2},'evidence':[
        clear,{**clear,'id':'v1','uncertain':True},{**clear,'id':'v2','ocr_unusable':True}]}),
        SimpleNamespace(id='old',source_id='other',version=1,payload={'provenance':{'pipeline_version':1},'evidence':[clear]})]
    class FakeSession:
        calls=0
        def scalars(self,query):
            self.calls+=1
            return SimpleNamespace(all=lambda:rows if self.calls==2 else [])
    chunks=snapshots(FakeSession())
    assert len(chunks)==1 and chunks[0]['origin']['evidence_id']=='v0'
    assert chunks[0]['content']=='Texto observado\nTexto visible: Una frase'


def test_index_resumes_only_confirmed_batches(client,indexed_source,database):
    from app.models import NoteRevision
    from uuid import uuid4
    with Session(database[0]) as session:
        session.add_all([NoteRevision(id=uuid4(),version=1,source_id=UUID(indexed_source['id']),content=f'Idea personal {i}') for i in range(129)])
        session.commit()
    calls=[]
    def interrupted(payload,cancelled):
        calls.append(len(payload['texts']))
        if len(calls)==2:raise Cancelled()
        return {'vectors':[VECTOR for _ in payload['texts']]}
    app.state.retrieval.runner=interrupted
    stopped=run(client,'index');assert stopped['status']=='stopped' and calls==[128,2]
    with Session(database[0]) as session:
        assert session.scalar(select(func.count()).select_from(ChunkEmbedding))==128
        assert len(missing_chunks(session,PROFILE['profile_id'])[0])==2
    app.state.retrieval.runner=lambda payload,cancelled:{'vectors':[VECTOR for _ in payload['texts']]}
    resumed=run(client,'index');assert resumed['status']=='completed' and resumed['added']==2


def test_retrieval_respects_current_project_membership(client,indexed_source):
    run(client,'index')
    project=client.post('/api/projects',json={'name':'Solo estas fuentes'}).json()
    url='/api/projects/'+project['id']+'/sources/'+indexed_source['id']
    client.put(url)
    def query():
        response=client.post('/api/retrieval/tasks',json={'action':'chat','query':'¿Qué dice?','project_id':project['id']})
        assert response.status_code==202,response.text
        finish(app.state.retrieval)
        return client.get('/api/retrieval/tasks/'+response.json()['id']).json()
    assert len(query()['selected'])==1
    client.delete(url)
    assert query()['selected']==[]


def test_scoped_summary_uses_partial_evidence_without_similarity_gate(client,indexed_source):
    run(client,'index');calls=[]
    def runner(payload,cancelled):
        calls.append(payload['action'])
        if payload['action']=='embed':return {'vectors':[[0.0,1.0]+[0.0]*1022]}
        return {'selected':[payload['hits'][0]['chunk_id']]}
    app.state.retrieval.runner=runner
    def ask(query):
        response=client.post('/api/retrieval/tasks',json={'action':'chat','query':query,'source_ids':[indexed_source['id']],'answer_mode':'extractive'})
        assert response.status_code==202,response.text
        finish(app.state.retrieval)
        return client.get('/api/retrieval/tasks/'+response.json()['id']).json()
    summary=ask('Resume los temas de este reel.')
    assert summary['selected'][0]['content']=='Texto comprobado' and calls==['select']
    assert summary['coverage']=={'method':'temporal_sample','sampled':1,'available':1}
    assert summary['hits'][0]['score'] is None
    unrelated=ask('¿Cuánta harina lleva el pan?')
    assert unrelated['selected']==[] and unrelated['coverage'] is None
    assert 'Muestra temporal: 1 de 1' in client.get('/api/retrieval/sessions/'+summary['session_id']+'/export').text
    greeting=client.post('/api/retrieval/tasks',json={'action':'chat','query':'hola','session_id':summary['session_id'],'source_ids':[indexed_source['id']],'answer_mode':'extractive'})
    help_task=client.get('/api/retrieval/tasks/'+greeting.json()['id']).json()
    assert help_task['scope']['source_ids']==[indexed_source['id']] and help_task['scope']['answer_mode']=='extractive'


def test_temporal_sample_is_bounded_live_and_preserves_stopped_scope(client,indexed_source,database):
    from app.models import NoteRevision
    from app.retrieval_data import sampled_overview
    from uuid import uuid4
    with Session(database[0]) as session:
        session.add_all([NoteRevision(id=uuid4(),version=1,source_id=UUID(indexed_source['id']),content=f'Idea {i}',start_ms=i*100,end_ms=i*100+1) for i in range(20)])
        session.commit()
    run(client,'index')
    with Session(database[0]) as session:
        hits,total=sampled_overview(session,PROFILE['profile_id'],[indexed_source['id']])
        assert total==21 and len(hits)==8 and len({h['chunk_id'] for h in hits})==8
        chunks=hydrate(session,hits);assert chunks[-1]['start_ms']==1900
        assert sampled_overview(session,'another-profile',[indexed_source['id']])==([],0)
        assert sampled_overview(session,PROFILE['profile_id'],[str(uuid4())])==([],0)
    app.state.retrieval.runner=lambda payload,cancelled:(_ for _ in ()).throw(Cancelled())
    response=client.post('/api/retrieval/tasks',json={'action':'chat','query':'Resume este reel','source_ids':[indexed_source['id']],'answer_mode':'extractive'})
    finish(app.state.retrieval)
    stopped=client.get('/api/retrieval/tasks/'+response.json()['id']).json()
    assert stopped['status']=='stopped' and stopped['scope']['source_ids']==[indexed_source['id']]
