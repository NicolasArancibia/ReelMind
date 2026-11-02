import threading,time
from uuid import uuid4
import pytest
from app.main import app
from app.downloads import supported,DownloadUnavailable
from app.download_task import public_url
from app.processing import Cancelled
from app.media import storage_path
from test_audio_engine import finish,result,prepared

def source(client,code):return client.post('/api/sources',json={'url':f'https://www.instagram.com/reel/{code}/'}).json()

def test_download_attach_analyze_and_retry_without_redownload(client,prepared,monkeypatch):
    item=source(client,'fixture');calls=[]
    def download(url,attempt,cancelled):
        calls.append(url);path=storage_path(f'work/{attempt}/download/video.mp4');path.parent.mkdir(parents=True);path.write_bytes(b'\x00\x00\x00\x18ftypisomfixture')
        return path,{'download_provider':'fixture'}
    monkeypatch.setattr('app.downloads.recover_video',download);prepared.runner=lambda *args:result()
    assert calls==[] and client.get('/api/processing').json()['state']=='stopped'
    client.post('/api/processing/start');finish(prepared)
    current=client.get('/api/sources/'+item['id']).json()
    assert current['job']['status']=='completed' and len(current['assets'])==1
    transcripts=client.get('/api/sources/'+item['id']+'/transcripts').json()
    assert transcripts[0]['provenance']['download_provider']=='fixture'
    client.put('/api/sources/'+item['id']+'/queue',json={'queued':True,'expected_updated_at':current['updated_at']})
    client.post('/api/processing/start');finish(prepared)
    assert len(calls)==1 and len(client.get('/api/sources/'+item['id']).json()['assets'])==1

def test_stop_during_download_blocks_other_heavy_work_and_keeps_link(client,prepared,monkeypatch):
    item=source(client,'cancel');entered=threading.Event()
    def download(url,attempt,cancelled):
        entered.set()
        while not cancelled():time.sleep(.01)
        raise Cancelled()
    monkeypatch.setattr('app.downloads.recover_video',download)
    client.post('/api/processing/start');assert entered.wait(3)
    assert client.post('/api/processing/start').status_code==409
    client.post('/api/processing/stop');finish(prepared)
    current=client.get('/api/sources/'+item['id']).json()
    assert current['original_url']==item['original_url'] and current['assets']==[] and current['job']['status']=='stopped'
    assert client.get('/api/processing').json()['state']=='stopped'

def test_failure_is_per_item_and_queue_continues(client,prepared,monkeypatch):
    first=source(client,'unavailable');second=source(client,'available')
    def download(url,attempt,cancelled):
        if '/unavailable/' in url:raise DownloadUnavailable('No disponible; adjunta copia.')
        path=storage_path(f'work/{attempt}/video.mp4');path.parent.mkdir(parents=True);path.write_bytes(b'\x00\x00\x00\x18ftypisomok');return path,{}
    monkeypatch.setattr('app.downloads.recover_video',download);prepared.runner=lambda *args:result()
    client.post('/api/processing/start');finish(prepared)
    assert client.get('/api/sources/'+first['id']).json()['job']['status']=='unavailable'
    assert client.get('/api/sources/'+second['id']).json()['job']['status']=='completed'

def test_supported_links_and_private_network_rejected(monkeypatch):
    assert supported('https://www.instagram.com/reel/example/')
    for url in ['https://example.org/reel/a','file:///a','https://www.instagram.com:123/reel/a','https://user:secret@instagram.com/reel/a']:
        assert not supported(url)
    monkeypatch.setattr('app.download_task.socket.getaddrinfo',lambda *a,**k:[(2,1,6,'',('127.0.0.1',443))])
    with pytest.raises(ValueError):public_url('https://example.org/video.mp4')

def test_copy_survives_analysis_stop_and_hash_is_shared(client,prepared,monkeypatch,database):
    first=source(client,'first');calls=[]
    def download(url,attempt,cancelled):
        calls.append(url);path=storage_path(f'work/{attempt}/download/video.mp4');path.parent.mkdir(parents=True);path.write_bytes(b'\x00\x00\x00\x18ftypisomsame');return path,{}
    monkeypatch.setattr('app.downloads.recover_video',download)
    def stop(*args):raise Cancelled()
    prepared.runner=stop;client.post('/api/processing/start');finish(prepared)
    saved=client.get('/api/sources/'+first['id']).json()
    assert len(saved['assets'])==1 and saved['job']['status']=='stopped'
    client.put('/api/sources/'+first['id']+'/queue',json={'queued':True,'expected_updated_at':saved['updated_at']})
    second=source(client,'second');prepared.runner=lambda *args:result()
    client.post('/api/processing/start');finish(prepared)
    a=client.get('/api/sources/'+first['id']).json();b=client.get('/api/sources/'+second['id']).json()
    assert len(calls)==2 and a['job']['status']==b['job']['status']=='completed'
    assert a['assets'][0]['file']['checksum']==b['assets'][0]['file']['checksum']
    from sqlalchemy.orm import Session
    from sqlalchemy import select,func
    from app.models import MediaFile
    with Session(database[0]) as session:assert session.scalar(select(func.count()).select_from(MediaFile))==1
