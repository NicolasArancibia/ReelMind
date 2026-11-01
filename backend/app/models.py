from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Source(Base):
    favorite: Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.false())
    summary: Mapped[str | None] = mapped_column(sa.Text)
    __tablename__ = "sources"
    __table_args__ = (
        sa.CheckConstraint(
            "platform IN ('instagram', 'youtube', 'tiktok', 'local', 'other')",
            name="ck_sources_platform",
        ),
        sa.CheckConstraint("source_type IN ('url', 'file')", name="ck_sources_type"),
        sa.CheckConstraint(
            "source_type <> 'url' OR (original_url IS NOT NULL AND btrim(original_url) <> '')",
            name="ck_sources_url_required",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'ready', 'needs_input', 'failed')", name="ck_sources_status"
        ),
        sa.Index(
            "uq_sources_canonical_url", "canonical_url", unique=True,
            postgresql_where=sa.text("canonical_url IS NOT NULL"),
        ),
        sa.Index("ix_sources_status_created_at", "status", "created_at"),
        sa.Index("ix_sources_platform", "platform"),
    )

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    platform: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source_type: Mapped[str] = mapped_column(sa.Text, nullable=False)
    original_url: Mapped[str | None] = mapped_column(sa.Text)
    canonical_url: Mapped[str | None] = mapped_column(sa.Text)
    title: Mapped[str | None] = mapped_column(sa.String(240))
    author: Mapped[str | None] = mapped_column(sa.Text)
    status: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    tags: Mapped[list["Tag"]] = relationship(secondary="source_tags", lazy="selectin", order_by="Tag.name")
    categories: Mapped[list["Category"]] = relationship(secondary="source_categories", lazy="selectin", order_by="Category.name")
    assets: Mapped[list["MediaAsset"]] = relationship(lazy="selectin", order_by="MediaAsset.created_at")
    job: Mapped["ProcessingJob | None"] = relationship(lazy="selectin", uselist=False)


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (sa.CheckConstraint("btrim(name) <> ''", name="ck_tags_name"),)
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(sa.String(60))
    normalized_name: Mapped[str] = mapped_column(sa.Text, unique=True)


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (sa.CheckConstraint("btrim(name) <> ''", name="ck_categories_name"),)
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(sa.String(60))
    normalized_name: Mapped[str] = mapped_column(sa.Text, unique=True)


source_tags = sa.Table("source_tags", Base.metadata,
    sa.Column("source_id", sa.Uuid, sa.ForeignKey("sources.id", ondelete="RESTRICT"), primary_key=True),
    sa.Column("tag_id", sa.Uuid, sa.ForeignKey("tags.id", ondelete="RESTRICT"), primary_key=True),
    sa.Index("ix_source_tags_tag", "tag_id"))
source_categories = sa.Table("source_categories", Base.metadata,
    sa.Column("source_id", sa.Uuid, sa.ForeignKey("sources.id", ondelete="RESTRICT"), primary_key=True),
    sa.Column("category_id", sa.Uuid, sa.ForeignKey("categories.id", ondelete="RESTRICT"), primary_key=True),
    sa.Index("ix_source_categories_category", "category_id"))


class MediaFile(Base):
    __tablename__ = "media_files"
    __table_args__ = (sa.CheckConstraint("size_bytes > 0", name="ck_media_files_size"),)
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    checksum: Mapped[str] = mapped_column(sa.String(64), unique=True)
    local_path: Mapped[str] = mapped_column(sa.Text, unique=True)
    mime_type: Mapped[str] = mapped_column(sa.Text)
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger)


class MediaAsset(Base):
    __tablename__ = "media_assets"
    __table_args__ = (
        sa.UniqueConstraint("source_id", "file_id", name="uq_media_assets_source_file"),
        sa.UniqueConstraint("id", "source_id", name="uq_media_assets_id_source"),
    )
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    source_id: Mapped[UUID] = mapped_column(sa.ForeignKey("sources.id", ondelete="RESTRICT"), index=True)
    file_id: Mapped[UUID] = mapped_column(sa.ForeignKey("media_files.id", ondelete="RESTRICT"), index=True)
    original_name: Mapped[str] = mapped_column(sa.String(240))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    file: Mapped[MediaFile] = relationship(lazy="selectin")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    __table_args__ = (
        sa.CheckConstraint("status IN ('pending', 'cancelled', 'running', 'completed', 'failed', 'stopped', 'unavailable')", name="ck_processing_jobs_status"),
        sa.Index("ix_processing_jobs_order", "status", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    source_id: Mapped[UUID] = mapped_column(sa.ForeignKey("sources.id", ondelete="RESTRICT"), unique=True)
    status: Mapped[str] = mapped_column(sa.Text, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    run_id: Mapped[UUID | None] = mapped_column(sa.Uuid)
    error_message: Mapped[str | None] = mapped_column(sa.Text)


class EngineState(Base):
    __tablename__ = "engine_state"
    __table_args__ = (
        sa.CheckConstraint("id = 1", name="ck_engine_singleton"),
        sa.CheckConstraint("state IN ('stopped', 'running', 'pause_requested', 'paused', 'stop_requested')", name="ck_engine_state"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[str] = mapped_column(sa.Text, server_default="stopped")
    run_id: Mapped[UUID | None] = mapped_column(sa.Uuid)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())


class ProcessingAttempt(Base):
    __tablename__ = "processing_attempts"
    __table_args__ = (sa.CheckConstraint("status IN ('running', 'completed', 'failed', 'stopped', 'unavailable')", name="ck_attempt_status"),)
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    job_id: Mapped[UUID] = mapped_column(sa.ForeignKey("processing_jobs.id", ondelete="RESTRICT"), index=True)
    status: Mapped[str] = mapped_column(sa.Text)
    started_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    finished_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(sa.Text)


class Transcript(Base):
    __tablename__ = "transcripts"
    __table_args__ = (
        sa.UniqueConstraint("source_id", "version", name="uq_transcript_version"),
        sa.UniqueConstraint('id', 'source_id', 'asset_id', name='uq_transcript_id_source_asset'),
        sa.UniqueConstraint('id', 'source_id', name='uq_transcript_id_source'),
        sa.CheckConstraint("version > 0 AND duration_ms >= 0", name="ck_transcript_numbers"),
        sa.CheckConstraint("outcome IN ('speech', 'no_speech', 'no_audio')", name="ck_transcript_outcome"),
        sa.ForeignKeyConstraint(["asset_id", "source_id"], ["media_assets.id", "media_assets.source_id"], name="fk_transcript_asset_source", ondelete="RESTRICT"),
    )
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    source_id: Mapped[UUID] = mapped_column(sa.ForeignKey("sources.id", ondelete="RESTRICT"), index=True)
    asset_id: Mapped[UUID] = mapped_column(sa.ForeignKey("media_assets.id", ondelete="RESTRICT"))
    attempt_id: Mapped[UUID] = mapped_column(sa.ForeignKey("processing_attempts.id", ondelete="RESTRICT"), unique=True)
    version: Mapped[int] = mapped_column()
    outcome: Mapped[str] = mapped_column(sa.Text)
    language: Mapped[str | None] = mapped_column(sa.Text)
    duration_ms: Mapped[int] = mapped_column(sa.BigInteger)
    provenance: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    segments: Mapped[list["TranscriptSegment"]] = relationship(lazy="selectin", order_by="TranscriptSegment.ordinal")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    __table_args__ = (
        sa.UniqueConstraint("transcript_id", "ordinal", name="uq_segment_ordinal"),
        sa.CheckConstraint("ordinal >= 0 AND start_ms >= 0 AND end_ms > start_ms", name="ck_segment_interval"),
    )
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    transcript_id: Mapped[UUID] = mapped_column(sa.ForeignKey("transcripts.id", ondelete="RESTRICT"), index=True)
    ordinal: Mapped[int] = mapped_column()
    start_ms: Mapped[int] = mapped_column(sa.BigInteger)
    end_ms: Mapped[int] = mapped_column(sa.BigInteger)
    text: Mapped[str] = mapped_column(sa.Text)


class AudiovisualAnalysis(Base):
    __tablename__ = 'audiovisual_analyses'
    __table_args__ = (
        sa.UniqueConstraint('id','source_id',name='uq_av_id_source'),
        sa.UniqueConstraint('source_id', 'version', name='uq_av_version'),
        sa.CheckConstraint('version > 0', name='ck_av_version'),
        sa.ForeignKeyConstraint(['transcript_id', 'source_id', 'asset_id'],
            ['transcripts.id', 'transcripts.source_id', 'transcripts.asset_id'], name='fk_av_transcript_source_asset', ondelete='RESTRICT'),
    )
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text('gen_random_uuid()'))
    source_id: Mapped[UUID] = mapped_column(sa.ForeignKey('sources.id', ondelete='RESTRICT'), index=True)
    asset_id: Mapped[UUID] = mapped_column(sa.ForeignKey('media_assets.id', ondelete='RESTRICT'))
    transcript_id: Mapped[UUID] = mapped_column(sa.ForeignKey('transcripts.id', ondelete='RESTRICT'), unique=True)
    version: Mapped[int] = mapped_column()
    payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())


from app.vector_type import Vector

class EmbeddingProfile(Base):
    __tablename__='embedding_profiles'
    __table_args__=(sa.CheckConstraint('dimensions = 1024',name='ck_embedding_dimensions'),)
    id: Mapped[str] = mapped_column(sa.String(64),primary_key=True)
    model: Mapped[str] = mapped_column(sa.Text)
    digest: Mapped[str] = mapped_column(sa.Text)
    dimensions: Mapped[int] = mapped_column()
    configuration: Mapped[dict] = mapped_column(JSONB)

class Project(Base):
    archived_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    __tablename__='projects'
    __table_args__=(sa.CheckConstraint('length(btrim(name)) > 0',name='ck_project_name'),)
    id: Mapped[UUID] = mapped_column(sa.Uuid,primary_key=True,server_default=sa.text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(sa.String(120))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True),server_default=sa.func.now())

class ProjectSource(Base):
    __tablename__='project_sources'
    project_id: Mapped[UUID] = mapped_column(sa.ForeignKey('projects.id',ondelete='RESTRICT'),primary_key=True)
    source_id: Mapped[UUID] = mapped_column(sa.ForeignKey('sources.id',ondelete='RESTRICT'),primary_key=True,index=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True),server_default=sa.func.now())

class RelationRevision(Base):
    from_note_id: Mapped[UUID | None] = mapped_column(sa.Uuid)
    from_note_version: Mapped[int | None] = mapped_column()
    to_note_id: Mapped[UUID | None] = mapped_column(sa.Uuid)
    to_note_version: Mapped[int | None] = mapped_column()
    __tablename__='relation_revisions'
    __table_args__=(sa.CheckConstraint("version > 0 AND (from_source_id <> to_source_id OR coalesce(from_note_id::text, '') <> coalesce(to_note_id::text, ''))",name='ck_relation_identity'),
        sa.CheckConstraint('(from_note_id IS NULL) = (from_note_version IS NULL)',name='ck_relation_from_note'),
        sa.CheckConstraint('(to_note_id IS NULL) = (to_note_version IS NULL)',name='ck_relation_to_note'),
        sa.ForeignKeyConstraint(['from_note_id','from_note_version','from_source_id'],['note_revisions.id','note_revisions.version','note_revisions.source_id'],name='fk_relation_from_note',ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['to_note_id','to_note_version','to_source_id'],['note_revisions.id','note_revisions.version','note_revisions.source_id'],name='fk_relation_to_note',ondelete='RESTRICT'),
        sa.CheckConstraint('length(btrim(label)) > 0 AND length(btrim(evidence)) > 0',name='ck_relation_evidence'),
        sa.CheckConstraint("review_status IN ('proposed','accepted','rejected')",name='ck_relation_review'))
    id: Mapped[UUID] = mapped_column(sa.Uuid,primary_key=True)
    version: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(sa.ForeignKey('projects.id',ondelete='RESTRICT'),index=True)
    from_source_id: Mapped[UUID] = mapped_column(sa.ForeignKey('sources.id',ondelete='RESTRICT'))
    to_source_id: Mapped[UUID] = mapped_column(sa.ForeignKey('sources.id',ondelete='RESTRICT'))
    label: Mapped[str] = mapped_column(sa.String(120))
    evidence: Mapped[str] = mapped_column(sa.String(2000))
    review_status: Mapped[str] = mapped_column(sa.String(20))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True),server_default=sa.func.now())

class ContentChunk(Base):
    note_id: Mapped[UUID | None] = mapped_column(sa.Uuid)
    note_version: Mapped[int | None] = mapped_column()
    __tablename__='content_chunks'
    __table_args__=(
        sa.UniqueConstraint('id','source_id',name='uq_chunk_id_source'),
        sa.CheckConstraint('num_nonnulls(analysis_id,transcript_id,note_id) = 1 AND ((note_id IS NULL) = (note_version IS NULL))',name='ck_chunk_origin'),
        sa.ForeignKeyConstraint(['note_id','note_version','source_id'],['note_revisions.id','note_revisions.version','note_revisions.source_id'],name='fk_chunk_note_source',ondelete='RESTRICT'),
        sa.CheckConstraint('ordinal >= 0 AND length(content) BETWEEN 1 AND 1200',name='ck_chunk_content'),
        sa.CheckConstraint('(start_ms IS NULL AND end_ms IS NULL) OR (start_ms IS NOT NULL AND end_ms IS NOT NULL AND start_ms >= 0 AND end_ms > start_ms)',name='ck_chunk_interval'),
        sa.CheckConstraint('time_ms IS NULL OR time_ms >= 0',name='ck_chunk_point'),
        sa.ForeignKeyConstraint(['analysis_id','source_id'],['audiovisual_analyses.id','audiovisual_analyses.source_id'],name='fk_chunk_analysis_source',ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['transcript_id','source_id'],['transcripts.id','transcripts.source_id'],name='fk_chunk_transcript_source',ondelete='RESTRICT'),
    )
    id: Mapped[UUID] = mapped_column(sa.Uuid,primary_key=True,server_default=sa.text('gen_random_uuid()'))
    source_id: Mapped[UUID] = mapped_column(sa.ForeignKey('sources.id',ondelete='RESTRICT'),index=True)
    analysis_id: Mapped[UUID | None] = mapped_column(sa.Uuid)
    transcript_id: Mapped[UUID | None] = mapped_column(sa.Uuid)
    origin_key: Mapped[str] = mapped_column(sa.Text,unique=True)
    ordinal: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(sa.Text)
    content_sha256: Mapped[str] = mapped_column(sa.String(64))
    start_ms: Mapped[int | None] = mapped_column(sa.BigInteger)
    end_ms: Mapped[int | None] = mapped_column(sa.BigInteger)
    time_ms: Mapped[int | None] = mapped_column(sa.BigInteger)
    origin: Mapped[dict] = mapped_column(JSONB)

class ChunkEmbedding(Base):
    __tablename__='chunk_embeddings'
    chunk_id: Mapped[UUID] = mapped_column(sa.ForeignKey('content_chunks.id',ondelete='RESTRICT'),primary_key=True)
    profile_id: Mapped[str] = mapped_column(sa.ForeignKey('embedding_profiles.id',ondelete='RESTRICT'),primary_key=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))

class ChatSession(Base):
    project_id: Mapped[UUID | None] = mapped_column(sa.ForeignKey('projects.id',ondelete='RESTRICT'))
    archived_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    __tablename__='chat_sessions'
    id: Mapped[UUID] = mapped_column(sa.Uuid,primary_key=True,server_default=sa.text('gen_random_uuid()'))
    title: Mapped[str] = mapped_column(sa.String(120))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True),server_default=sa.func.now())

class RetrievalTask(Base):
    __tablename__='retrieval_tasks'
    __table_args__=(sa.CheckConstraint("action IN ('index','search','chat')",name='ck_retrieval_action'),
        sa.CheckConstraint("status IN ('running','stop_requested','completed','failed','stopped')",name='ck_retrieval_state'))
    id: Mapped[UUID] = mapped_column(sa.Uuid,primary_key=True,server_default=sa.text('gen_random_uuid()'))
    action: Mapped[str] = mapped_column(sa.Text)
    status: Mapped[str] = mapped_column(sa.Text)
    query: Mapped[str] = mapped_column(sa.String(800),server_default='')
    session_id: Mapped[UUID | None] = mapped_column(sa.ForeignKey('chat_sessions.id',ondelete='RESTRICT'))
    profile_id: Mapped[str] = mapped_column(sa.String(64))
    result: Mapped[dict] = mapped_column(JSONB,server_default='{}')
    error_message: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True),server_default=sa.func.now())
    finished_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

class NoteRevision(Base):
    __tablename__='note_revisions'
    __table_args__=(sa.UniqueConstraint('id','version','source_id',name='uq_note_version_source'),
        sa.ForeignKeyConstraint(['quote_chunk_id','source_id'],['content_chunks.id','content_chunks.source_id'],ondelete='RESTRICT',name='fk_note_quote_source',use_alter=True),
        sa.CheckConstraint('version > 0 AND length(btrim(content)) > 0',name='ck_note_content'),
        sa.CheckConstraint('(start_ms IS NULL AND end_ms IS NULL) OR (start_ms IS NOT NULL AND start_ms >= 0 AND end_ms IS NOT NULL AND end_ms > start_ms)',name='ck_note_interval'))
    id: Mapped[UUID] = mapped_column(sa.Uuid,primary_key=True)
    version: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[UUID] = mapped_column(sa.ForeignKey('sources.id',ondelete='RESTRICT'),index=True)
    content: Mapped[str] = mapped_column(sa.String(8000))
    quote_chunk_id: Mapped[UUID | None] = mapped_column(sa.Uuid)
    quote_text: Mapped[str | None] = mapped_column(sa.Text)
    start_ms: Mapped[int | None] = mapped_column(sa.BigInteger)
    end_ms: Mapped[int | None] = mapped_column(sa.BigInteger)
    favorite: Mapped[bool] = mapped_column(sa.Boolean,server_default=sa.false())
    archived: Mapped[bool] = mapped_column(sa.Boolean,server_default=sa.false())
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True),server_default=sa.func.now())
