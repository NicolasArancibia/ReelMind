from uuid import uuid4
from test_audio_engine import upload

def test_membership_idempotent_and_source_preserved(client):
    source=upload(client)
    p=client.post('/api/projects',json={'name':' Ideas '});assert p.status_code==201
    project=p.json();assert project['name']=='Ideas'
    url=f"/api/projects/{project['id']}/sources"
    for _ in range(2): assert client.put(url+'/'+source['id']).status_code==200
    assert [m['id'] for m in client.get(url).json()]==[source['id']]
    client.delete(url+'/'+source['id'])
    assert client.get(url).json()==[]
    assert client.get('/api/sources/'+source['id']).status_code==200
    assert client.get('/api/projects').json()==[project]

def test_invalid_membership_and_trash_restoration(client):
    assert client.post('/api/projects',json={'name':'   '}).status_code==422
    project=client.post('/api/projects',json={'name':'Proyecto'}).json()
    url=f"/api/projects/{project['id']}/sources"
    assert client.put(url+'/'+str(uuid4())).status_code==404
    source=upload(client);client.put(url+'/'+source['id'])
    client.request('DELETE','/api/sources/'+source['id'],json={'expected_updated_at':source['updated_at']})
    assert client.get(url).json()==[]
    assert client.put(url+'/'+source['id']).status_code==404
    trashed=client.get('/api/sources?view=trash').json()['items'][0]
    client.post('/api/sources/'+source['id']+'/restore',json={'expected_updated_at':trashed['updated_at']})
    assert client.get(url).json()[0]['id']==source['id']
