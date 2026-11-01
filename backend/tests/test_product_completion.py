import json
from uuid import uuid4
import pytest
from test_audio_engine import upload
from test_graph import setup_graph
from app.retrieval_task import grounded_answer
from app.maintenance import temporary_candidates,clean_temporaries
from app.maintenance_window import store_configuration,validate_recovery


def test_batch_atomicity_taxonomy_and_export(client):
    sources=[upload(client,'batch-a.mp4'),upload(client,'batch-b.mp4')]
    ids=[s['id'] for s in sources]
    def batch(action,**extra):return client.post('/api/library/actions',json={'source_ids':ids,'action':action,**extra})
    assert batch('labels',tags=['Memoria'],categories=['Aprender']).json()['analysis_started'] is False
    labels=client.get('/api/organization').json();tag=labels['tags'][0]
    stale=client.get('/api/sources/'+ids[0]).json()['updated_at']
    assert client.put('/api/system/taxonomy/tags/'+tag['id'],json={'name':'Recuerdos','expected_name':tag['name']}).json()['sources_updated']==2
    assert client.put('/api/system/taxonomy/tags/'+tag['id'],json={'name':'Otra','expected_name':tag['name']}).status_code==409
    assert client.get('/api/sources/'+ids[0]).json()['updated_at']!=stale
    broken=client.post('/api/library/actions',json={'source_ids':ids+[str(uuid4())],'action':'favorite'})
    assert broken.status_code==409
    assert client.get('/api/sources?favorite=true').json()['total']==0
    assert batch('favorite').status_code==200
    assert client.get('/api/sources?favorite=true').json()['total']==2
    assert batch('enqueue').status_code==200
    assert client.get('/api/processing').json()['state']=='stopped'
    status=client.get('/api/system/status');assert status.status_code==200,status.text
    data=client.get('/api/system/export').json()['tables']
    assert len(data['sources'])==2 and 'chunk_embeddings' not in data


def test_personal_idea_connections_keep_pinned_revision(client):
    url,sources,payload=setup_graph(client)
    note_url='/api/sources/'+sources[0]['id']+'/notes'
    note=client.post(note_url,json={'content':'Conectar una idea con su fuente'}).json()
    relation=client.post(url+'/relations',json={**payload,'from_note_id':note['id'],'from_note_version':1})
    assert relation.status_code==201,relation.text
    revised=client.put(note_url+'/'+note['id'],json={**note,'content':'Idea corregida','expected_version':1}).json()
    graph=client.get(url+'/graph').json()
    assert graph['relations'][0]['from_node_id']==f"note:{note['id']}:v1"
    assert any(n['id']==f"note:{note['id']}:v2" for n in graph['nodes'])
    hidden=client.put(note_url+'/'+note['id'],json={**revised,'archived':True,'expected_version':2}).json()
    assert client.get(url+'/graph').json()['relations']==[]
    client.put(note_url+'/'+note['id'],json={**hidden,'archived':False,'expected_version':3})
    assert client.get(url+'/graph').json()['relations'][0]['version']==1


def test_help_session_scope_archive_and_pagination(client):
    project=client.post('/api/projects',json={'name':'Contexto'}).json()
    def hello(**extra):return client.post('/api/retrieval/tasks',json={'action':'chat','query':'hola',**extra})
    first=hello(project_id=project['id']);assert first.status_code==202
    task=client.get('/api/retrieval/tasks/'+first.json()['id']).json()
    assert task['help'] and task['hits']==[]
    sid=task['session_id']
    assert hello(session_id=sid).status_code==409
    assert hello(session_id=sid,project_id=project['id']).status_code==202
    edit={'title':'Preguntas del proyecto','archived':True,'expected_title':'hola','expected_archived':False}
    assert client.put('/api/retrieval/sessions/'+sid,json=edit).status_code==200
    assert client.put('/api/retrieval/sessions/'+sid,json=edit).status_code==409
    assert client.get('/api/retrieval/sessions').json()==[]
    assert len(client.get('/api/retrieval/sessions?archived=true&q=proyecto&offset=0&limit=1').json())==1
    assert hello(session_id=sid,project_id=project['id']).status_code==404
    assert client.get('/api/retrieval/sessions/'+sid+'/export').status_code==200


class Provider:
    def __init__(self,claim,supported=True):self.claim=claim;self.supported=supported;self.calls=0
    def chat(self,*args,**kwargs):
        self.calls+=1
        return {'claims':[self.claim]} if self.calls==1 else {'supported':self.supported}

def test_grounded_reply_rejects_invented_quote_numbers_and_unsupported_claim():
    hit={'chunk_id':'one','content':'La memoria mejora con ejemplos.','time_ms':37000,'origin':{'kind':'audio'}}
    valid={'text':'El vídeo habla de aprender con ejemplos.','quote':'mejora con ejemplos','chunk_id':'one'}
    assert grounded_answer(Provider(valid),'¿Qué dice?',[hit])['selected']==['one']
    for claim,verdict in [({**valid,'quote':'cita inventada'},True),({**valid,'text':'Mejora un 80 por ciento.'},True),(valid,False)]:
        with pytest.raises(ValueError):grounded_answer(Provider(claim,verdict),'¿Qué dice?',[hit])


def test_config_switch_preserves_credentials_and_validates_report(tmp_path):
    runtime=tmp_path/'runtime.json';credentials=tmp_path/'secrets'/'app.xml';credentials.parent.mkdir()
    original={'CredentialPath':str(credentials),'DataRoot':str(tmp_path/'old'),'PythonPath':'retained'}
    runtime.write_text(json.dumps(original))
    history=store_configuration({'DataRoot':str(tmp_path/'new'),'DatabaseName':'reelmind_restore_'+uuid4().hex},runtime)
    assert json.loads(history.read_text())==original
    assert json.loads(runtime.read_text())['CredentialPath']==str(credentials)
    with pytest.raises(ValueError):store_configuration({'DatabaseName':'dbname=postgres'},runtime)
    report=tmp_path/'verification.json';(tmp_path/'data').mkdir()
    report.write_text(json.dumps({'verified':True,'database':'reelmind','data_root':str(tmp_path/'data')}))
    with pytest.raises(ValueError):validate_recovery(report)


def test_cleanup_revalidates_whole_selection_and_never_media(tmp_path,monkeypatch):
    folder=tmp_path/'work'/str(uuid4());folder.mkdir(parents=True)
    temporary=folder/'result.json';temporary.write_text('{}')
    original=tmp_path/'media'/'original.mp4';original.parent.mkdir();original.write_bytes(b'original')
    rows=temporary_candidates(tmp_path);assert len(rows)==1
    selection=tmp_path/'selection.json';selection.write_text(json.dumps(rows+[{'relative':'media/original.mp4'}]))
    monkeypatch.setattr('app.maintenance.ensure_stopped',lambda:None)
    class Engine:
        def dispose(self):pass
    monkeypatch.setattr('app.maintenance.get_engine',lambda:Engine())
    monkeypatch.setattr('app.maintenance.ManualEngine.acquire',lambda self:object())
    monkeypatch.setattr('app.maintenance.ManualEngine.release',lambda lock:None)
    with pytest.raises(ValueError):clean_temporaries(selection)
    assert temporary.exists() and original.exists()
    selection.write_text(json.dumps(rows));clean_temporaries(selection)
    assert not temporary.exists() and original.read_bytes()==b'original'
