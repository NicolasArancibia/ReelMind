from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from test_audio_engine import upload

def setup_graph(client):
    sources=[upload(client,'graph-a.mp4'),upload(client,'graph-b.mp4')]
    project=client.post('/api/projects',json={'name':'Grafo'}).json()
    url=f"/api/projects/{project['id']}"
    for s in sources: client.put(url+'/sources/'+s['id'])
    payload={'from_source_id':sources[0]['id'],'to_source_id':sources[1]['id'],'label':'Complementa',
        'evidence':'Nota manual: comparar el primer minuto de ambas fuentes.','review_status':'proposed'}
    return url,sources,payload

def test_revision_history_conflict_and_rejected_retained(client):
    url,sources,payload=setup_graph(client)
    response=client.post(url+'/relations',json=payload);assert response.status_code==201
    relation=response.json();edit_url=url+'/relations/'+relation['id']
    correction={**payload,'label':'Contrasta','evidence':'Corrección manual del vínculo.','expected_version':1,'review_status':'accepted'}
    assert client.put(edit_url,json=correction).json()['version']==2
    assert client.put(edit_url,json=correction).status_code==409
    assert client.put(edit_url,json={**correction,'expected_version':2,'review_status':'rejected'}).status_code==200
    graph=client.get(url+'/graph').json();row=graph['relations'][0]
    assert row['version']==3 and len(row['history'])==3
    assert row['history'][0]['label']=='Complementa' and row['history'][0]['evidence']==payload['evidence']
    assert row['review_status']=='rejected' and len(graph['nodes'])==2
    assert all(client.get('/api/sources/'+s['id']).status_code==200 for s in sources)

def test_hidden_sources_and_membership_preserve_history(client):
    url,sources,payload=setup_graph(client);client.post(url+'/relations',json=payload)
    client.delete(url+'/sources/'+sources[0]['id'])
    assert client.get(url+'/graph').json()['relations']==[]
    client.put(url+'/sources/'+sources[0]['id'])
    assert len(client.get(url+'/graph').json()['relations'])==1
    s=client.get('/api/sources/'+sources[0]['id']).json()
    client.request('DELETE','/api/sources/'+s['id'],json={'expected_updated_at':s['updated_at']})
    assert client.get(url+'/graph').json()['relations']==[]
    assert client.post(url+'/relations',json=payload).status_code==409

def test_invalid_cross_project_and_self_relations(client):
    url,sources,payload=setup_graph(client)
    assert client.post(url+'/relations',json={**payload,'to_source_id':sources[0]['id']}).status_code==422
    assert client.post(url+'/relations',json={**payload,'evidence':'  '}).status_code==422
    assert client.post(url+'/relations',json={**payload,'to_source_id':str(uuid4())}).status_code==409
    other=client.post('/api/projects',json={'name':'Otro'}).json()
    assert client.post(f"/api/projects/{other['id']}/relations",json=payload).status_code==409
    assert client.get(url+'/graph').json()['relations']==[]

def test_concurrent_corrections_only_one_wins(client):
    url,sources,payload=setup_graph(client)
    row=client.post(url+'/relations',json=payload).json()
    def correct(label):return client.put(url+'/relations/'+row['id'],json={**payload,'expected_version':1,'label':label}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool: statuses=list(pool.map(correct,['Una','Otra']))
    assert sorted(statuses)==[200,409]
    assert len(client.get(url+'/graph').json()['relations'][0]['history'])==2
