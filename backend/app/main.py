from contextlib import asynccontextmanager
from typing import Literal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import get_settings
from app.db import get_engine, get_session
from app.models import Source
from app.schemas import SourceCreate, SourceMutation, SourcePage, SourceRead, SourceUpdate, url_adapter

REVISION = "0001_sources"
ALLOWED_ORIGINS = {
    "http://127.0.0.1:5180", "http://localhost:5180",
    "http://127.0.0.1:8000", "http://localhost:8000",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()  # Reject accidental autostart or nonlocal configuration.
    yield
    get_engine().dispose()


app = FastAPI(title="ReelMind", version="0.2.0", lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])


@app.middleware("http")
async def local_origin_only(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin is not None and origin not in ALLOWED_ORIGINS:
        return JSONResponse(status_code=403, content={"detail": "Origen no permitido."})
    return await call_next(request)


@app.exception_handler(SQLAlchemyError)
async def database_unavailable(request: Request, exc: SQLAlchemyError):
    # Never serialize DB exception details, SQL parameters, credentials or connection URLs.
    return JSONResponse(status_code=503, content={"detail": "La base local no está disponible. Comprueba PostgreSQL e inténtalo nuevamente."})


@app.exception_handler(RequestValidationError)
async def invalid_input(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Revisa los datos enviados. El enlace debe ser http o https, sin contraseñas; el título admite hasta 240 caracteres. Si estabas editando, actualiza la biblioteca."})


def platform_for(host: str) -> str:
    for domain, platform in (
        ("instagram.com", "instagram"), ("youtube.com", "youtube"),
        ("youtu.be", "youtube"), ("tiktok.com", "tiktok"),
    ):
        if host == domain or host.endswith("." + domain):
            return platform
    return "other"


@app.get("/api/health")
def health(session: Session = Depends(get_session)):
    revision = session.scalar(text("SELECT version_num FROM alembic_version"))
    if revision != REVISION:
        raise HTTPException(503, "Falta actualizar la base local con las migraciones.")
    session.scalar(select(func.count()).select_from(Source))
    return {
        "status": "ok", "database": "connected", "schema_revision": revision,
        "processing": {"state": "stopped", "available": False, "autostart": False, "concurrency": 1},
    }


@app.get("/api/sources", response_model=SourcePage)
def list_sources(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=2_147_483_647),
    view: Literal["library", "trash"] = "library",
    session: Session = Depends(get_session),
):
    # Counts and page share one snapshot, even when another tab changes the library.
    session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
    active_total, trash_total = session.execute(select(
        func.count().filter(Source.deleted_at.is_(None)),
        func.count().filter(Source.deleted_at.is_not(None)),
    )).one()
    total = trash_total if view == "trash" else active_total
    offset = min(offset, ((max(total, 1) - 1) // limit) * limit)
    visible = Source.deleted_at.is_not(None) if view == "trash" else Source.deleted_at.is_(None)
    sort_date = Source.deleted_at if view == "trash" else Source.created_at
    items = session.scalars(select(Source).where(visible).order_by(sort_date.desc(), Source.id.desc()).offset(offset).limit(limit)).all()
    return {"items": items, "total": total, "active_total": active_total,
            "trash_total": trash_total, "offset": offset, "limit": limit}


@app.get("/api/sources/{source_id}", response_model=SourceRead)
def get_source(source_id: UUID, session: Session = Depends(get_session)):
    source = session.get(Source, source_id)
    if source is None or source.deleted_at is not None:
        raise HTTPException(404, "No encontramos ese enlace.")
    return source


@app.post("/api/sources", response_model=SourceRead, status_code=201)
def create_source(payload: SourceCreate, session: Session = Depends(get_session)):
    parsed = url_adapter.validate_python(payload.url)
    source = Source(
        original_url=payload.url, canonical_url=str(parsed),
        source_type="url", platform=platform_for(parsed.host or ""), title=payload.title,
    )
    session.add(source)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if constraint == "uq_sources_canonical_url":
            existing = session.scalar(select(Source).where(Source.canonical_url == str(parsed)))
            if existing is not None and existing.deleted_at is not None:
                return JSONResponse(status_code=409, content={
                    "detail": "Este enlace está en la papelera. Puedes restaurarlo conservando sus datos.",
                    "existing_source": SourceRead.model_validate(existing).model_dump(mode="json"),
                })
            raise HTTPException(409, "Este enlace ya está guardado en tu biblioteca.") from None
        raise
    session.refresh(source)
    return source


def locked_source(session: Session, source_id: UUID) -> Source:
    source = session.scalar(select(Source).where(Source.id == source_id).with_for_update())
    if source is None:
        raise HTTPException(404, "No encontramos ese enlace.")
    return source


def check_version(source: Source, payload: SourceMutation):
    if source.updated_at != payload.expected_updated_at:
        raise HTTPException(409, "Este enlace cambió en otra ventana. Cierra este cuadro y actualiza la biblioteca antes de volver a intentarlo.")


def commit_source(session: Session, source: Source) -> Source:
    # Use statement time, not transaction start time, after obtaining the row lock.
    source.updated_at = func.clock_timestamp()
    session.commit()
    session.refresh(source)
    return source


@app.patch("/api/sources/{source_id}", response_model=SourceRead)
def update_source(source_id: UUID, payload: SourceUpdate, session: Session = Depends(get_session)):
    source = locked_source(session, source_id)
    check_version(source, payload)
    if source.deleted_at is not None:
        raise HTTPException(409, "Restaura el enlace desde la papelera antes de editarlo.")
    source.title = payload.title
    return commit_source(session, source)


@app.delete("/api/sources/{source_id}", response_model=SourceRead)
def trash_source(source_id: UUID, payload: SourceMutation, session: Session = Depends(get_session)):
    source = locked_source(session, source_id)
    if source.deleted_at is not None:
        return source  # Retrying a confirmed deletion is harmless.
    check_version(source, payload)
    source.deleted_at = func.clock_timestamp()
    return commit_source(session, source)


@app.post("/api/sources/{source_id}/restore", response_model=SourceRead)
def restore_source(source_id: UUID, payload: SourceMutation, session: Session = Depends(get_session)):
    source = locked_source(session, source_id)
    if source.deleted_at is None:
        return source
    check_version(source, payload)
    source.deleted_at = None
    return commit_source(session, source)
