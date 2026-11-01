from uuid import UUID
import subprocess

import imageio_ffmpeg
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audiovisual import Observation, Synthesis, analyze, sampled_frames, normalized_observation
from app.main import app
from app.models import AudiovisualAnalysis, Transcript
from app.processing import Cancelled
from test_audio_engine import upload, result, requeue, finish


class Vision:
    def observe(self, image):
        assert image[:2] == b'\xff\xd8'
        return Observation(description='Fondo rojo.', visible_text='', uncertain=False)

class Text:
    def synthesize(self, evidence):
        return Synthesis.model_validate({'claims': [{'text': 'Se ve rojo.', 'evidence_ids': ['v0']}], 'limitations': ['Muestreo parcial.']})


def make_video(path):
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-f', 'lavfi', '-i',
                    'color=c=red:s=320x180:r=10', '-t', '2', '-an', str(path)], check=True)


def test_frame_sampling_and_evidence_context(tmp_path):
    path = tmp_path / 'fixture.mp4'; make_video(path)
    frames = list(sampled_frames(path))
    assert len(frames) == 8
    assert [t for t, _ in frames] == sorted(set(t for t, _ in frames))
    assert all(0 <= t < 2000 for t, _ in frames)
    value = analyze(path, result(), Vision(), Text())
    assert len(value['evidence']) == 9
    assert value['coverage']['partial'] is True
    assert value['evidence'][0]['frame_sha256']


def test_ocr_normalization_only_removes_exact_duplicate_lines():
    row = normalized_observation(Observation(description='Texto', visible_text='Muse\nDots\nMuse\nmuse', uncertain=False))
    assert row['visible_text'] == 'Muse\nDots\nmuse'
    assert row['ocr_repeated_lines_removed'] == 1
    assert len(row['raw_ocr_sha256']) == 64


def test_unusable_ocr_is_explicit_and_never_silently_rewritten():
    row = normalized_observation(Observation(description='Texto del fotograma.', visible_text='Original'+r'\n'*10, uncertain=False))
    assert row['visible_text'] == '' and row['ocr_unusable'] and row['uncertain']
    assert row['description'] == 'Texto del fotograma.'


def test_unknown_evidence_and_unstructured_output_rejected(tmp_path):
    path = tmp_path / 'fixture.mp4'; make_video(path)
    class WrongText:
        def synthesize(self, evidence):
            return Synthesis.model_validate({'claims': [{'text': 'Inventado', 'evidence_ids': ['v999']}], 'limitations': ['Parcial']})
    with pytest.raises(ValueError, match='inexistentes'):
        analyze(path, result(), Vision(), WrongText())
    with pytest.raises(ValueError):
        Observation.model_validate({'description': 'x', 'visible_text': '', 'uncertain': 'false'})


def test_av_mode_versions_and_same_source_fk(client, monkeypatch, database):
    source = upload(client)
    processor = app.state.processor
    monkeypatch.setattr('app.processing.ready', lambda: True)
    monkeypatch.setattr('app.local_ai.prepared', lambda root: True)
    value = {**result(), 'analysis': {'evidence': [], 'synthesis': {'claims': [], 'limitations': ['test']}}}
    calls = []
    def runner(asset, attempt, cancelled, mode):
        calls.append(mode); return value
    monkeypatch.setattr('app.processing.run_audio', runner)
    assert client.post('/api/processing/start?mode=audiovisual').status_code == 200
    finish(processor)
    url = f'/api/sources/{source["id"]}/analyses'
    first = client.get(url).json()
    assert len(first) == 1 and first[0]['version'] == 1
    requeue(client, source)
    client.post('/api/processing/start?mode=audiovisual'); finish(processor)
    assert [r['version'] for r in client.get(url).json()] == [2, 1]
    assert calls == ['audiovisual', 'audiovisual']
    other = upload(client, 'other.mp4')
    processor.runner = lambda *args: result()
    client.post('/api/processing/start'); finish(processor)
    with Session(database[0]) as session:
        transcript = session.scalar(select(Transcript).where(Transcript.source_id == UUID(other['id'])))
        session.add(AudiovisualAnalysis(source_id=UUID(source['id']), asset_id=transcript.asset_id,
            transcript_id=transcript.id, version=3, payload={}))
        with pytest.raises(IntegrityError) as failure: session.commit()
        assert failure.value.orig.diag.constraint_name == 'fk_av_transcript_source_asset'


def test_missing_models_invalid_mode_and_cancellation(client, monkeypatch):
    processor = app.state.processor
    monkeypatch.setattr('app.processing.ready', lambda: True)
    monkeypatch.setattr('app.local_ai.prepared', lambda root: False)
    assert client.post('/api/processing/start?mode=audiovisual').status_code == 409
    assert client.post('/api/processing/start?mode=cloud').status_code == 422
    source = upload(client)
    monkeypatch.setattr('app.local_ai.prepared', lambda root: True)
    def cancelled(*args): raise Cancelled()
    monkeypatch.setattr('app.processing.run_audio', cancelled)
    client.post('/api/processing/start?mode=audiovisual'); finish(processor)
    assert client.get(f'/api/sources/{source["id"]}/analyses').json() == []
    assert client.get(f'/api/sources/{source["id"]}/transcripts').json() == []
    assert client.get('/api/processing').json()['state'] == 'stopped'
