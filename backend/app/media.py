"""Copy-only imports. Published blobs are never deleted after an uncertain commit."""
import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.models import MediaAsset, MediaFile, ProcessingJob, Source
from app.schemas import SourceRead

router = APIRouter()


def storage_path(relative: str) -> Path:
    root = get_settings().data_root.resolve()
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or ".." in Path(relative).parts or not path.is_relative_to(root) or path == root:
        raise HTTPException(409, "Ruta de almacenamiento no válida.")
    return path


def media_type(name: str, header: bytes) -> str:
    extension = Path(name).suffix.lower()
    if extension in {".mp4", ".m4v", ".mov"} and len(header) >= 12 and header[4:8] == b"ftyp":
        return "video/quicktime" if extension == ".mov" else "video/mp4"
    if extension in {".webm", ".mkv"} and header.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm" if extension == ".webm" else "video/x-matroska"
    if extension == ".avi" and header.startswith(b"RIFF") and header[8:12] == b"AVI ":
        return "video/x-msvideo"
    raise HTTPException(415, "Usa MP4, MOV, M4V, WebM, MKV o AVI con una cabecera de vídeo válida.")


def publish_file(staged: Path, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staged, destination)


@router.post("/api/imports", response_model=SourceRead, status_code=201)
async def import_video(
    request: Request,
    filename: str = Query(min_length=1, max_length=240),
    source_id: UUID | None = None,
    expected_updated_at: str | None = None,
    session: Session = Depends(get_session),
):
    from app.main import check_version, commit_source, locked_source
    from app.schemas import SourceMutation
    from pydantic import ValidationError

    if any(c in filename for c in ('/', '\\', ':')) or any(ord(c) < 32 for c in filename):
        raise HTTPException(422, "El nombre debe ser un archivo, sin rutas.")
    mutation = None
    if source_id is not None:
        try:
            mutation = SourceMutation(expected_updated_at=expected_updated_at)
        except ValidationError:
            raise HTTPException(422, "Actualiza la fuente antes de adjuntar el vídeo.") from None
    limit = get_settings().max_upload_bytes
    length = request.headers.get("content-length")
    if length and (not length.isdecimal() or int(length) > limit):
        raise HTTPException(413, "El archivo supera el límite de importación (2 GiB por defecto).")
    staged = storage_path(f"staging/{uuid4().hex}.part")
    try:
        staged.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        size = 0
        header = b""
        with staged.open("xb") as output:
            async for chunk in request.stream():
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, "El archivo supera el límite de importación.")
                header = (header + chunk[:32])[:32]
                digest.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        mime = media_type(filename, header)
        checksum = digest.hexdigest()
        relative = f"media/{checksum[:2]}/{checksum}"
        destination = storage_path(relative)
        # One transaction publishes a given content hash at a time, across API processes.
        lock_key = int.from_bytes(bytes.fromhex(checksum[:16]), "big", signed=True)
        session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_key})
        physical = session.scalar(select(MediaFile).where(MediaFile.checksum == checksum))
        source = None
        if source_id is not None:
            source = locked_source(session, source_id)
            check_version(source, mutation)
            if source.deleted_at is not None:
                raise HTTPException(409, "Restaura la fuente antes de adjuntar archivos.")
        elif physical is not None:
            source = session.scalar(select(Source).join(MediaAsset).where(MediaAsset.file_id == physical.id, Source.source_type == "file"))
        # A repeated import also repairs a missing/corrupt managed copy using the supplied bytes.
        # Never remove a promoted file on rollback: a connection failure may hide a successful commit.
        publish_file(staged, destination)
        if physical is None:
            physical = MediaFile(checksum=checksum, local_path=relative, mime_type=mime, size_bytes=size)
            session.add(physical)
            session.flush()
        if source_id is None and source is not None:
            session.commit()
            return JSONResponse(status_code=409, content={
                "detail": "Este vídeo ya está guardado." if source.deleted_at is None else "Este vídeo está en la papelera. Puedes restaurarlo.",
                "existing_source": SourceRead.model_validate(source).model_dump(mode="json"),
            })
        if source is None:
            source = Source(source_type="file", platform="local", title=filename, job=ProcessingJob())
            session.add(source)
            session.flush()
        exists = session.scalar(select(MediaAsset).where(MediaAsset.source_id == source.id, MediaAsset.file_id == physical.id))
        if exists is None:
            session.add(MediaAsset(source_id=source.id, file_id=physical.id, original_name=filename))
        result = commit_source(session, source)
        session.expire(result, ["assets"])
        return result
    except OSError:
        session.rollback()
        raise HTTPException(507, "No se pudo guardar la copia local. Revisa espacio y permisos; el archivo original se conserva.") from None
    finally:
        # Only this request's UUID temporary is eligible for cleanup.
        try:
            staged.unlink(missing_ok=True)
        except OSError:
            pass  # Interrupted temporaries are retained for explicit maintenance, never auto-purged.


@router.get("/api/assets/{asset_id}/content")
def asset_content(asset_id: UUID, session: Session = Depends(get_session)):
    asset = session.get(MediaAsset, asset_id)
    if asset is None:
        raise HTTPException(404, "No encontramos ese archivo.")
    source = session.get(Source, asset.source_id)
    if source.deleted_at is not None:
        raise HTTPException(404, "Restaura la fuente para abrir sus archivos.")
    path = storage_path(asset.file.local_path)
    try:
        if not path.is_file() or path.stat().st_size != asset.file.size_bytes:
            raise HTTPException(409, "La copia local falta o cambió. Vuelve a importar el mismo archivo para recuperarla.")
    except OSError:
        raise HTTPException(409, "No se puede leer la copia local. Revisa sus permisos.") from None
    return FileResponse(path, media_type=asset.file.mime_type, filename=asset.original_name,
                        content_disposition_type="inline", headers={"X-Content-Type-Options": "nosniff"})
