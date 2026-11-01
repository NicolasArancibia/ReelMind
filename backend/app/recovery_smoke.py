"""Read-only API checks against an explicitly isolated restored database."""
import json
from fastapi.testclient import TestClient
from app.config import get_settings
from app.main import app


def main():
    settings=get_settings()
    if not settings.pg_database.startswith('reelmind_restore_'): raise ValueError('Solo una base aislada de restauración.')
    with TestClient(app) as client:
        health=client.get('/api/health').json()
        assert health['status']=='ok' and health['processing']['state']=='stopped'
        sources=client.get('/api/sources?limit=100').json()['items']
        assets=0
        for source in sources:
            assert client.get(f"/api/notes?source_id={source['id']}").status_code==200
            assert client.get(f"/api/sources/{source['id']}/export?format=json").status_code==200
            for kind in ('transcripts','analyses'):
                assert client.get(f"/api/sources/{source['id']}/{kind}").status_code==200
            for asset in source['assets']:
                response=client.get(f"/api/assets/{asset['id']}/content",headers={'Range':'bytes=0-15'})
                assert response.status_code==206 and len(response.content)==16
                assets+=1
        sessions=client.get('/api/retrieval/sessions').json()
        for session in sessions: assert client.get('/api/retrieval/sessions/'+session['id']).status_code==200
        projects=client.get('/api/projects').json()
        for project in projects:
            graph=client.get('/api/projects/'+project['id']+'/graph')
            assert graph.status_code==200
        assert client.get('/api/retrieval/status').json()['current'] is None
        assert client.get('/api/system/status').status_code==200
        assert client.post('/api/projects',json={'name':'blocked'},headers={'Origin':'https://example.org'}).status_code==403
        assert client.get('/api/health',headers={'Host':'untrusted.example'}).status_code==400
    report={'api_verified':True,'sources':len(sources),'media_ranges':assets,'sessions':len(sessions),'projects':len(projects),
        'engine':'stopped','cross_origin_write':'blocked','untrusted_host':'blocked'}
    (settings.data_root.parent/'api-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__': main()
