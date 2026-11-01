from uuid import UUID
from sqlalchemy.orm import Session
from app.models import NoteRevision,ContentChunk
from app.notebook import latest_notes
from app.retrieval_data import snapshots
from app.retrieval import save_index
from test_audio_engine import upload,result,finish
from test_retrieval import VECTOR,PROFILE
from app.main import app

def test_note_versions_archive_search_export_and_conflict(client,database):
    source=upload(client);url=f"/api/sources/{source['id']}/notes"
    first=client.post(url,json={'content':'Idea personal sobre memoria','start_ms':100,'end_ms':600,'favorite':True})
    assert first.status_code==201,first.text
    note=first.json();edit=url+'/'+note['id']
    corrected=client.put(edit,json={**note,'content':'Aprender con ejemplos','expected_version':1})
    assert corrected.status_code==200 and corrected.json()['version']==2
    assert client.put(edit,json={**note,'content':'Obsoleto','expected_version':1}).status_code==409
    assert client.get('/api/notes?q=ejemplos').json()['total']==1
    assert client.get(edit+'/history').json()[0]['content']=='Idea personal sobre memoria'
    assert client.put(edit,json={**corrected.json(),'archived':True,'expected_version':2}).status_code==200
    assert client.get('/api/notes').json()['total']==0
    assert client.get('/api/notes?archived=true').json()['total']==1
    exported=client.get(f"/api/sources/{source['id']}/export?format=json").json()
    assert exported['notes'][0]['archived'] and exported['notes'][0]['version']==3
    assert client.get('/api/sources/'+source['id']).status_code==200

def test_exact_quote_same_source_and_indexed_note_revision(client,database,monkeypatch):
    source=upload(client);other=upload(client,'other-note.mp4')
    monkeypatch.setattr('app.processing.ready',lambda:True);app.state.processor.runner=lambda *args:result()
    client.post('/api/processing/start');finish(app.state.processor)
    with Session(database[0]) as session:
        rows=snapshots(session);save_index(session,PROFILE,rows,[VECTOR for _ in rows]);session.commit()
        quote=session.query(ContentChunk).filter(ContentChunk.source_id==UUID(source['id'])).first();quote_id=str(quote.id)
    url=f"/api/sources/{source['id']}/notes"
    assert client.post(url,json={'content':'Fuera del vídeo','start_ms':0,'end_ms':9999999}).status_code==422
    response=client.post(url,json={'content':'Mi comentario','quote_chunk_id':quote_id})
    assert response.status_code==201 and response.json()['quote_text']=='Texto comprobado'
    assert client.post(f"/api/sources/{other['id']}/notes",json={'content':'Cita ajena','quote_chunk_id':quote_id}).status_code==422
    with Session(database[0]) as session:
        notes=[r for r in snapshots(session) if r['origin']['kind']=='note']
        assert len(notes)==1 and notes[0]['note_version']==1 and 'Texto comprobado' in notes[0]['content']
        save_index(session,PROFILE,notes,[VECTOR]);session.commit()
    note=response.json();client.put(url+'/'+note['id'],json={**note,'content':'Revisado','expected_version':1})
    with Session(database[0]) as session:
        from app.retrieval_data import ranked
        hits=ranked(session,PROFILE['profile_id'],VECTOR)
        assert len(hits)==2  # Original transcripts remain; obsolete note is excluded.

def test_invalid_intervals_and_summary_concurrency(client):
    source=upload(client);url=f"/api/sources/{source['id']}"
    for times in ({'start_ms':1},{'end_ms':10},{'start_ms':5,'end_ms':5}):assert client.post(url+'/notes',json={'content':'Nota',**times}).status_code==422
    body={'favorite':True,'summary':'Mi resumen','expected_updated_at':source['updated_at']}
    assert client.put(url+'/details',json=body).status_code==200
    assert client.put(url+'/details',json=body).status_code==409
    assert client.get('/api/sources?favorite=true&q=resumen').json()['total']==1
