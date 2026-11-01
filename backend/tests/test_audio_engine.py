from concurrent.futures import ThreadPoolExecutor
import json
import subprocess
import sys
import threading
import time
from uuid import UUID

import pytest
from sqlalchemy import select, text, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.models import Source, ProcessingJob, ProcessingAttempt, EngineState, Transcript
from app.processing import ManualEngine, HEAVY_LOCK, Cancelled
from app.process_guard import ProcessGuard


def upload(client, name="sample.mp4"):
    return client.post('/api/imports', params={"filename": name}, content=b'\x00\x00\x00\x18ftypisom' + name.encode()).json()


def result():
    return {"outcome": "speech", "language": "es", "duration_ms": 2000, "provenance": {"model": "test"},
            "segments": [{"start_ms": 0, "end_ms": 1000, "text": "Texto comprobado"}]}


@pytest.fixture
def prepared(client, monkeypatch):
    monkeypatch.setattr("app.processing.ready", lambda: True)
    return app.state.processor


def finish(processor):
    processor.thread.join(10)
    assert not processor.thread.is_alive()


def requeue(client, source):
    source = client.get(f'/api/sources/{source["id"]}').json()
    response = client.put(f'/api/sources/{source["id"]}/queue', json={"queued": True, "expected_updated_at": source["updated_at"]})
    assert response.status_code == 200
    return response.json()


def test_completed_versions_and_no_implicit_retry(client, prepared, database):
    source = upload(client)
    prepared.runner = lambda *args: result()
    assert client.post('/api/processing/start').status_code == 200
    finish(prepared)
    transcript_url = f'/api/sources/{source["id"]}/transcripts'
    first = client.get(transcript_url).json()
    assert len(first) == 1 and first[0]["segments"][0]["text"] == "Texto comprobado"
    assert first[0]["asset_id"] == source["assets"][0]["id"]
    assert first[0]["provenance"]["source_sha256"] == source["assets"][0]["file"]["checksum"]
    client.post('/api/processing/start'); finish(prepared)
    assert client.get(transcript_url).json() == first
    requeue(client, source)
    client.post('/api/processing/start'); finish(prepared)
    rows = client.get(transcript_url).json()
    assert [r["version"] for r in rows] == [2, 1] and rows[1] == first[0]
    database[0].dispose()
    assert client.get(transcript_url).json() == rows


def test_pause_finishes_current_and_requires_explicit_resume(client, prepared):
    sources = [upload(client, f'{i}.mp4') for i in range(2)]
    entered, release = threading.Event(), threading.Event()
    def runner(*args):
        entered.set(); assert release.wait(5); return result()
    prepared.runner = runner
    client.post('/api/processing/start'); assert entered.wait(5)
    assert client.post('/api/processing/pause').json()["state"] == "pause_requested"
    release.set(); finish(prepared)
    assert client.get('/api/processing').json()["state"] == "paused"
    assert [client.get(f'/api/sources/{s["id"]}').json()["job"]["status"] for s in sources] == ["completed", "pending"]
    client.post('/api/processing/start'); finish(prepared)
    assert client.get(f'/api/sources/{sources[1]["id"]}').json()["job"]["status"] == "completed"


def test_stop_cancels_without_partial_transcript_and_preserves_pending(client, prepared):
    sources = [upload(client, f'{i}.mp4') for i in range(2)]
    entered = threading.Event()
    def runner(asset, attempt_id, cancelled):
        entered.set()
        while not cancelled():
            time.sleep(.01)
        raise Cancelled()
    prepared.runner = runner
    client.post('/api/processing/start'); assert entered.wait(5)
    assert client.post('/api/processing/stop').status_code == 200
    finish(prepared)
    assert client.get('/api/processing').json()["state"] == "stopped"
    assert [client.get(f'/api/sources/{s["id"]}').json()["job"]["status"] for s in sources] == ["stopped", "pending"]
    assert client.get(f'/api/sources/{sources[0]["id"]}/transcripts').json() == []


def test_concurrent_start_and_cross_process_global_exclusion(client, prepared, database):
    upload(client)
    entered, release = threading.Event(), threading.Event()
    def runner(*args):
        entered.set(); assert release.wait(5); return result()
    prepared.runner = runner
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: client.post('/api/processing/start'), range(2)))
    assert sorted(r.status_code for r in responses) == [200, 409]
    assert entered.wait(5)
    other = ManualEngine(database[0])
    assert other.recover() is False
    code = "from app.db import get_engine; from sqlalchemy import text; c=get_engine().connect(); print(c.scalar(text('SELECT pg_try_advisory_lock(:k)'), {'k': " + str(HEAVY_LOCK) + "}))"
    probe = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=5)
    assert probe.returncode == 0 and probe.stdout.strip() == 'False'
    release.set(); finish(prepared)
    assert other.recover() is True


def test_new_import_restore_and_requeue_do_not_join_running_batch(client, prepared):
    first = upload(client)
    restored = upload(client, 'restore.mp4')
    trashed = client.request('DELETE', f'/api/sources/{restored["id"]}', json={"expected_updated_at": restored["updated_at"]}).json()
    entered, release = threading.Event(), threading.Event()
    def runner(*args):
        entered.set(); assert release.wait(5); return result()
    prepared.runner = runner
    client.post('/api/processing/start'); assert entered.wait(5)
    late = upload(client, 'later.mp4')
    client.post(f'/api/sources/{restored["id"]}/restore', json={"expected_updated_at": trashed["updated_at"]})
    running = client.get(f'/api/sources/{first["id"]}').json()
    assert client.put(f'/api/sources/{first["id"]}/queue', json={"queued": False, "expected_updated_at": running["updated_at"]}).status_code == 409
    assert client.request('DELETE', f'/api/sources/{first["id"]}', json={"expected_updated_at": running["updated_at"]}).status_code == 409
    release.set(); finish(prepared)
    for source in (late, restored):
        assert client.get(f'/api/sources/{source["id"]}').json()["job"]["status"] == "pending"


def test_failed_attempt_is_preserved_and_retry_is_manual(client, prepared, database):
    source = upload(client)
    def fail(*args):
        raise RuntimeError('secret diagnostic must not escape')
    prepared.runner = fail
    client.post('/api/processing/start'); finish(prepared)
    failed = client.get(f'/api/sources/{source["id"]}')
    assert failed.json()["job"]["status"] == 'failed' and 'secret' not in failed.text
    prepared.runner = lambda *args: result()
    client.post('/api/processing/start'); finish(prepared)
    assert client.get(f'/api/sources/{source["id"]}').json()["job"]["status"] == 'failed'
    requeue(client, source); client.post('/api/processing/start'); finish(prepared)
    with Session(database[0]) as session:
        assert sorted(session.scalars(select(ProcessingAttempt.status))) == ['completed', 'failed']


def test_recovery_after_crash_never_requeues_or_starts(client, prepared, database):
    source = upload(client)
    with Session(database[0]) as session:
        job = session.scalar(select(ProcessingJob))
        job.status = 'running'
        session.add(ProcessingAttempt(job_id=job.id, status='running'))
        session.get(EngineState, 1).state = 'running'
        session.commit()
    restarted = ManualEngine(database[0])
    assert restarted.recover()
    assert client.get('/api/processing').json()['state'] == 'stopped'
    assert client.get(f'/api/sources/{source["id"]}').json()['job']['status'] == 'stopped'
    with Session(database[0]) as session:
        attempt = session.scalar(select(ProcessingAttempt))
        assert attempt.status == 'stopped' and attempt.finished_at is not None


def test_unavailable_url_and_multiple_assets_are_explicit(client, prepared):
    source = client.post('/api/sources', json={"url": "https://example.com/inaccessible"}).json()
    client.post('/api/processing/start'); finish(prepared)
    assert client.get(f'/api/sources/{source["id"]}').json()['job']['status'] == 'unavailable'
    assert client.get(f'/api/sources/{source["id"]}/transcripts').json() == []


def test_windows_guard_terminates_descendants(tmp_path):
    import psutil
    pid_file = tmp_path / 'child.pid'
    code = "import subprocess, sys, time; from pathlib import Path; sys.stdin.buffer.read(1); p=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(60)"
    process = subprocess.Popen([sys.executable, '-c', code, str(pid_file)], stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    with ProcessGuard(process):
        process.stdin.write(b'1'); process.stdin.flush()
        deadline = time.monotonic() + 5
        while not pid_file.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        child_id = int(pid_file.read_text())
        assert psutil.pid_exists(child_id)
    process.wait(timeout=5)
    assert not psutil.pid_exists(child_id)


def test_transcript_integrity_and_atomic_failed_commit(client, prepared, database):
    source = upload(client)
    invalid = result(); invalid['segments'][0]['end_ms'] = 0
    prepared.runner = lambda *args: invalid
    client.post('/api/processing/start'); finish(prepared)
    assert client.get(f'/api/sources/{source["id"]}/transcripts').json() == []
    with Session(database[0]) as session:
        assert session.scalar(select(func.count()).select_from(Transcript)) == 0
        assert session.scalar(select(ProcessingJob.status)) == 'stopped'


def test_asset_provenance_cannot_point_at_another_source(client, prepared, database):
    first, second = upload(client, 'first.mp4'), upload(client, 'second.mp4')
    prepared.runner = lambda *args: result()
    client.post('/api/processing/start'); finish(prepared)
    with Session(database[0]) as session:
        row = session.scalar(select(Transcript).where(Transcript.source_id == UUID(first['id'])))
        row.asset_id = UUID(second['assets'][0]['id'])
        with pytest.raises(IntegrityError):
            session.commit()


def test_guard_kills_heavy_process_when_supervisor_crashes(tmp_path):
    import psutil
    pid_file = tmp_path / 'guarded.pid'
    code = "import subprocess,sys,time; from pathlib import Path; from app.process_guard import ProcessGuard; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); guard=ProcessGuard(p); Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(60)"
    supervisor = subprocess.Popen([sys.executable, '-c', code, str(pid_file)], creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        deadline = time.monotonic() + 5
        while not pid_file.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        child_id = int(pid_file.read_text())
        assert psutil.pid_exists(child_id)
        supervisor.kill(); supervisor.wait(timeout=5)
        deadline = time.monotonic() + 5
        while psutil.pid_exists(child_id) and time.monotonic() < deadline:
            time.sleep(.02)
        assert not psutil.pid_exists(child_id)
    finally:
        if supervisor.poll() is None:
            supervisor.kill(); supervisor.wait(timeout=5)
