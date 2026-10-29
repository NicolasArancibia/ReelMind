from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Source(Base):
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
