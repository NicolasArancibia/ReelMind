from contextlib import asynccontextmanager
from typing import Literal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import get_settings
from app.db import get_engine, get_session
from app.models import Source, Tag, Category, ProcessingJob, MediaAsset
from app.schemas import SourceCreate, SourceMutation, SourcePage, SourceRead, SourceUpdate, url_adapter
from app.schemas import OrganizationUpdate, QueueUpdate

REVISION = "0008_graph"
ALLOWED_ORIGINS = {
    "http://127.0.0.1:5180", "http://localhost:5180",
    "http://127.0.0.1:8000", "http://localhost:8000",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()  # Reject accidental autostart or nonlocal configuration.
    from app.processing import ManualEngine
    from app.retrieval import RetrievalEngine
    app.state.processor = ManualEngine(get_engine())
    app.state.retrieval = RetrievalEngine(get_engine())
    try:
        with get_engine().connect() as connection:
            migrated = connection.scalar(text("SELECT version_num FROM alembic_version")) == REVISION
        if migrated:
            app.state.processor.recover()
            app.state.retrieval.recover()
    except SQLAlchemyError:
        pass  # Health reports missing DB/schema; the library can show the recovery message.
    yield
    app.state.processor.close()
    app.state.retrieval.close()
    get_engine().dispose()


app = FastAPI(title="ReelMind", version="0.4.0", lifespan=lifespan)
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
    return JSONResponse(status_code=422, content={"detail": "Revisa los datos: enlaces http/https sin contraseñas; título hasta 240 caracteres; hasta 20 etiquetas y 10 categorías de 1–60 caracteres. Si estabas editando, actualiza la biblioteca."})


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
    from app.processing import engine_status
    return {
        "status": "ok", "database": "connected", "schema_revision": revision,
        "processing": engine_status(session),
    }


@app.get("/api/sources", response_model=SourcePage)
def list_sources(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=2_147_483_647),
    view: Literal["library", "trash", "queue"] = "library",
    q: str = Query(default="", max_length=240),
    platform: Literal["instagram", "youtube", "tiktok", "local", "other"] | None = None,
    source_type: Literal["url", "file"] | None = None,
    tag: UUID | None = None,
    category: UUID | None = None,
    session: Session = Depends(get_session),
):
    # Counts and page share one snapshot, even when another tab changes the library.
    session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
    active_total, trash_total = session.execute(select(
        func.count().filter(Source.deleted_at.is_(None)),
        func.count().filter(Source.deleted_at.is_not(None)),
    )).one()
    visible = Source.deleted_at.is_not(None) if view == "trash" else Source.deleted_at.is_(None)
    queued = Source.job.has(ProcessingJob.status == "pending")
    queue_total = session.scalar(select(func.count()).select_from(Source).where(Source.deleted_at.is_(None), queued))
    conditions = [visible]
    if view == "queue":
        conditions.append(queued)
    if platform:
        conditions.append(Source.platform == platform)
    if source_type:
        conditions.append(Source.source_type == source_type)
    if tag:
        conditions.append(Source.tags.any(Tag.id == tag))
    if category:
        conditions.append(Source.categories.any(Category.id == category))
    if q.strip():
        pattern = "%" + q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        conditions.append(or_(Source.title.ilike(pattern), Source.original_url.ilike(pattern),
            Source.tags.any(Tag.name.ilike(pattern)), Source.categories.any(Category.name.ilike(pattern)),
            Source.assets.any(MediaAsset.original_name.ilike(pattern))))
    total = session.scalar(select(func.count()).select_from(Source).where(*conditions))
    offset = min(offset, ((max(total, 1) - 1) // limit) * limit)
    sort_date = Source.deleted_at if view == "trash" else Source.created_at
    query = select(Source).where(*conditions)
    if view == "queue":
        query = query.join(ProcessingJob).order_by(ProcessingJob.created_at, ProcessingJob.id)
    else:
        query = query.order_by(sort_date.desc(), Source.id.desc())
    items = session.scalars(query.offset(offset).limit(limit)).all()
    return {"items": items, "total": total, "active_total": active_total,
            "trash_total": trash_total, "queue_total": queue_total, "offset": offset, "limit": limit}


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
    source.job = ProcessingJob()
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
    if source.job and source.job.status == "running":
        raise HTTPException(409, "Detén el motor antes de enviar esta fuente a la papelera.")
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
    if source.job:
        source.job.run_id = None  # Restoration never joins a running batch.
    return commit_source(session, source)


@app.get("/api/organization")
def organization(session: Session = Depends(get_session)):
    return {key: [{"id": row.id, "name": row.name} for row in session.scalars(select(model).order_by(model.name))]
            for key, model in (("tags", Tag), ("categories", Category))}


@app.put("/api/sources/{source_id}/organization", response_model=SourceRead)
def organize(source_id: UUID, payload: OrganizationUpdate, session: Session = Depends(get_session)):
    source = locked_source(session, source_id)
    check_version(source, payload)
    if source.deleted_at is not None:
        raise HTTPException(409, "Restaura la fuente antes de organizarla.")
    for key, model in (("tags", Tag), ("categories", Category)):
        values = []
        # Stable order prevents deadlocks when different sources create the same names.
        for name in sorted(getattr(payload, key), key=str.casefold):
            normalized = name.casefold()
            session.execute(insert(model).values(name=name, normalized_name=normalized).on_conflict_do_nothing(index_elements=["normalized_name"]))
            values.append(session.scalar(select(model).where(model.normalized_name == normalized)))
        setattr(source, key, values)
    return commit_source(session, source)


@app.put("/api/sources/{source_id}/queue", response_model=SourceRead)
def queue_source(source_id: UUID, payload: QueueUpdate, session: Session = Depends(get_session)):
    source = locked_source(session, source_id)
    check_version(source, payload)
    if source.deleted_at is not None:
        raise HTTPException(409, "Restaura la fuente antes de cambiar la cola.")
    if source.job is None:
        source.job = ProcessingJob()
    if source.job.status == "running":
        raise HTTPException(409, "Detén el motor antes de cambiar este trabajo.")
    if payload.queued and source.job.status != "pending":
        source.job.created_at = func.clock_timestamp()
    source.job.run_id = None
    source.job.error_message = None
    source.job.status = "pending" if payload.queued else "cancelled"
    return commit_source(session, source)


from app.media import router as media_router
app.include_router(media_router)
from app.processing import router as processing_router
app.include_router(processing_router)
from app.retrieval import router as retrieval_router
app.include_router(retrieval_router)
from app.projects import router as projects_router
app.include_router(projects_router)
