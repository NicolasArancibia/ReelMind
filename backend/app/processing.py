"""Manual engine. PostgreSQL session lock covers claim, process tree and final commit."""
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, text, update, func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.media import storage_path
from app.models import EngineState, ProcessingJob, ProcessingAttempt, Source, Transcript, TranscriptSegment, AudiovisualAnalysis
from app.process_guard import ProcessGuard

# Shared by every future heavy consumer, including chat. Not a row/queue-only lock.
HEAVY_LOCK = 0x5245454C4D494E44
router = APIRouter()


class Cancelled(Exception):
    pass


def model_path():
    return storage_path(f"models/{get_settings().whisper_model}")


def ready():
    path = model_path()
    return all((path / name).is_file() for name in ("model.bin", "config.json", "tokenizer.json", "reelmind-model.json"))


def run_audio(asset, attempt_id, cancelled, mode='audio'):
    work = storage_path(f"work/{attempt_id}")
    work.mkdir(parents=True, exist_ok=False)
    path = storage_path(asset.file.local_path)
    if not path.is_file():
        raise FileNotFoundError()
    # The decoder has no database secret and cannot download models implicitly.
    env = {k: v for k, v in os.environ.items() if k not in {"PGPASSWORD", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"}}
    env.update(HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
    process = subprocess.Popen([sys.executable, "-m", "app.audio_task", str(path), str(work),
                                str(model_path()), asset.file.checksum, mode], stdin=subprocess.PIPE,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
                               cwd=Path(__file__).resolve().parents[1],
                               creationflags=subprocess.CREATE_NO_WINDOW)
    started = time.monotonic()
    try:
        with ProcessGuard(process):
            process.stdin.write(b"1"); process.stdin.flush(); process.stdin.close()
            while process.poll() is None:
                if cancelled():
                    raise Cancelled()
                if time.monotonic() - started > get_settings().audio_timeout_seconds:
                    raise TimeoutError()
                time.sleep(0.2)
            if cancelled():
                raise Cancelled()
            if process.returncode:
                raise RuntimeError("decoder")
            result = json.loads((work / "result.json").read_text(encoding="utf-8"))
            if "error" in result:
                raise RuntimeError("decoder")
            return result
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        # Only our known files, no recursive cleanup or originals.
        for name in ("audio.wav", "result.json", "evidence.json", "progress.json"):
            try:
                (work / name).unlink(missing_ok=True)
            except OSError:
                pass
        try:
            work.rmdir()
        except OSError:
            pass


class ManualEngine:
    def __init__(self, database, runner=run_audio):
        self.database, self.runner = database, runner
        self.thread = None
        self.shutdown = threading.Event()

    def acquire(self):
        connection = self.database.connect()
        try:
            acquired = connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": HEAVY_LOCK})
            connection.commit()
            if acquired:
                return connection
        except BaseException:
            connection.close()
            raise
        connection.close()
        return None

    @staticmethod
    def release(connection):
        try:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": HEAVY_LOCK})
            connection.commit()
        finally:
            connection.close()

    def recover_rows(self, session):
        state = session.get(EngineState, 1, with_for_update=True)
        state.state = "stopped"; state.run_id = None; state.updated_at = func.clock_timestamp()
        message = "Ejecución interrumpida. Añade a pendientes e inicia para reintentar."
        interrupted = select(ProcessingJob.source_id).where(ProcessingJob.status == "running")
        session.execute(update(Source).where(Source.id.in_(interrupted)).values(status="needs_input", updated_at=func.clock_timestamp()))
        session.execute(update(ProcessingJob).where(ProcessingJob.status == "running").values(status="stopped", error_message=message))
        session.execute(update(ProcessingAttempt).where(ProcessingAttempt.status == "running").values(status="stopped", error_message=message, finished_at=func.clock_timestamp()))

    def recover(self):
        connection = self.acquire()
        if connection is None:
            return False
        try:
            with Session(connection) as session:
                self.recover_rows(session); session.commit()
            return True
        finally:
            self.release(connection)

    def start(self, mode='audio'):
        from app.local_ai import prepared
        if mode not in {'audio', 'audiovisual'}:
            raise HTTPException(422, 'Modo no válido.')
        if mode == 'audiovisual' and not prepared(get_settings().data_root):
            raise HTTPException(409, 'Falta preparar visión y síntesis locales. Consulta scripts/prepare-av.ps1.')
        if not ready():
            raise HTTPException(409, "Falta preparar el modelo de audio local. Ejecuta scripts/prepare-audio.ps1.")
        connection = self.acquire()
        if connection is None:
            raise HTTPException(409, "Los recursos están reservados por otra tarea pesada. Espera o detén el motor.")
        try:
            run_id = uuid4()
            with Session(connection) as session:
                self.recover_rows(session)
                ids = select(Source.id).where(Source.deleted_at.is_(None))
                session.execute(update(ProcessingJob).where(ProcessingJob.status == "pending", ProcessingJob.source_id.in_(ids)).values(run_id=run_id))
                state = session.get(EngineState, 1)
                state.state = "running"; state.run_id = run_id
                session.commit()
            self.shutdown.clear()
            self.thread = threading.Thread(target=self.loop, args=(connection, run_id, mode), daemon=True)
            self.thread.start()
        except BaseException:
            self.release(connection)
            raise

    def close(self):
        self.shutdown.set()
        if self.thread:
            self.thread.join(timeout=15)

    def loop(self, connection, run_id, mode='audio'):
        try:
            while not self.shutdown.is_set():
                with Session(connection, expire_on_commit=False) as session:
                    state = session.get(EngineState, 1, with_for_update=True)
                    if state.state != "running":
                        break
                    source = session.scalar(select(Source).join(ProcessingJob).where(
                        Source.deleted_at.is_(None), ProcessingJob.status == "pending", ProcessingJob.run_id == run_id
                    ).order_by(ProcessingJob.created_at, ProcessingJob.id).with_for_update(of=Source))
                    if source is None:
                        break
                    job = source.job
                    job.status = "running"; job.error_message = None
                    source.updated_at = func.clock_timestamp()
                    attempt = ProcessingAttempt(job_id=job.id, status="running")
                    session.add(attempt); session.flush()
                    source_id, attempt_id, job_id = source.id, attempt.id, job.id
                    asset = source.assets[0] if len(source.assets) == 1 else None
                    session.commit()
                def cancelled():
                    if self.shutdown.is_set():
                        return True
                    with Session(connection) as session:
                        return session.get(EngineState, 1).state == "stop_requested"
                result, error, status = None, None, "completed"
                try:
                    if asset is None:
                        status = "unavailable"
                        error = "Adjunta una copia local del vídeo para transcribir." if not source.assets else "Hay varias copias asociadas; crea una fuente local del archivo que deseas transcribir."
                    else:
                        result = self.runner(asset, attempt_id, cancelled) if mode == 'audio' else run_audio(asset, attempt_id, cancelled, mode)
                except Cancelled:
                    status, error = "stopped", "Detenido por solicitud. Añade a pendientes para reintentar."
                except Exception:
                    status, error = "failed", "No se pudo procesar la copia local. Revisa archivo, modelo, espacio y tiempo límite; añade a pendientes para reintentar."
                with Session(connection) as session:
                    state = session.get(EngineState, 1, with_for_update=True)
                    if state.state == "stop_requested" or self.shutdown.is_set():
                        status, error, result = "stopped", "Detenido por solicitud. Añade a pendientes para reintentar.", None
                    source = session.get(Source, source_id, with_for_update=True)
                    job, attempt = session.get(ProcessingJob, job_id), session.get(ProcessingAttempt, attempt_id)
                    if result is not None and status == "completed":
                        version = (session.scalar(select(func.max(Transcript.version)).where(Transcript.source_id == source_id)) or 0) + 1
                        transcript = Transcript(source_id=source_id, asset_id=asset.id, attempt_id=attempt_id,
                            version=version, outcome=result["outcome"], language=result["language"], duration_ms=result["duration_ms"],
                            provenance={**result["provenance"], "source_sha256": asset.file.checksum, "original_name": asset.original_name})
                        transcript.segments = [TranscriptSegment(ordinal=i, **row) for i, row in enumerate(result["segments"])]
                        session.add(transcript)
                        if 'analysis' in result:
                            session.flush()
                            analysis_version = (session.scalar(select(func.max(AudiovisualAnalysis.version)).where(AudiovisualAnalysis.source_id == source_id)) or 0) + 1
                            session.add(AudiovisualAnalysis(source_id=source_id, asset_id=asset.id,
                                transcript_id=transcript.id, version=analysis_version, payload=result['analysis']))
                    job.status = attempt.status = status
                    job.error_message = attempt.error_message = error
                    attempt.finished_at = func.clock_timestamp()
                    source.status = "ready" if status == "completed" else "needs_input" if status in {"unavailable", "stopped"} else "failed"
                    source.updated_at = func.clock_timestamp()
                    session.commit()
        except Exception:
            # A lost DB connection must never keep decoding or release work to another task early.
            connection.rollback()
        finally:
            try:
                with Session(connection) as session:
                    state = session.get(EngineState, 1, with_for_update=True)
                    paused = state.state == "pause_requested" and not self.shutdown.is_set()
                    self.recover_rows(session)
                    state.state = "paused" if paused else "stopped"
                    session.commit()
            finally:
                self.release(connection)


def engine_status(session):
    from app.local_ai import prepared
    state = session.get(EngineState, 1)
    active = session.scalar(select(ProcessingJob).where(ProcessingJob.status == "running"))
    return {"state": state.state, "available": ready(), "autostart": False, "concurrency": 1,
            "active_source_id": str(active.source_id) if active else None,
            "model": get_settings().whisper_model, "device": "cpu", "compute_type": "int8",
            "audiovisual_available": prepared(get_settings().data_root)}


@router.get("/api/processing")
def status(session: Session = Depends(get_session)):
    return engine_status(session)


@router.post("/api/processing/{action}")
def control(action: str, request: Request, mode: str = 'audio', session: Session = Depends(get_session)):
    if action == "start":
        request.app.state.processor.start(mode)
    elif action in {"pause", "stop"}:
        state = session.get(EngineState, 1, with_for_update=True)
        if state.state in {"running", "pause_requested", "stop_requested"}:
            if action == "stop" or state.state != "stop_requested":
                state.state = "stop_requested" if action == "stop" else "pause_requested"
        elif action == "stop":
            state.state = "stopped"
        state.updated_at = func.clock_timestamp()
        session.commit()
    else:
        raise HTTPException(404, "Control no disponible.")
    return engine_status(session)


@router.get("/api/sources/{source_id}/transcripts")
def transcripts(source_id: str, session: Session = Depends(get_session)):
    from uuid import UUID
    try:
        source = session.get(Source, UUID(source_id))
    except ValueError:
        raise HTTPException(422, "Identificador no válido.") from None
    if source is None or source.deleted_at is not None:
        raise HTTPException(404, "No encontramos esa fuente.")
    rows = session.scalars(select(Transcript).where(Transcript.source_id == source.id).order_by(Transcript.version.desc())).all()
    return [{"id": row.id, "version": row.version, "outcome": row.outcome, "language": row.language,
             "asset_id": row.asset_id, "duration_ms": row.duration_ms, "created_at": row.created_at,
             "provenance": row.provenance, "segments": [{"start_ms": s.start_ms, "end_ms": s.end_ms, "text": s.text} for s in row.segments]} for row in rows]


@router.get('/api/sources/{source_id}/analyses')
def analyses(source_id: str, session: Session = Depends(get_session)):
    from uuid import UUID
    try:
        source = session.get(Source, UUID(source_id))
    except ValueError:
        raise HTTPException(422, 'Identificador no válido.') from None
    if source is None or source.deleted_at is not None:
        raise HTTPException(404, 'No encontramos esa fuente.')
    rows = session.scalars(select(AudiovisualAnalysis).where(AudiovisualAnalysis.source_id == source.id).order_by(AudiovisualAnalysis.version.desc())).all()
    return [{"id": r.id, "version": r.version, "asset_id": r.asset_id, "transcript_id": r.transcript_id,
             "created_at": r.created_at, **r.payload} for r in rows]
