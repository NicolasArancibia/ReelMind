from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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
    __table_args__ = (sa.UniqueConstraint("source_id", "file_id", name="uq_media_assets_source_file"),)
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    source_id: Mapped[UUID] = mapped_column(sa.ForeignKey("sources.id", ondelete="RESTRICT"), index=True)
    file_id: Mapped[UUID] = mapped_column(sa.ForeignKey("media_files.id", ondelete="RESTRICT"), index=True)
    original_name: Mapped[str] = mapped_column(sa.String(240))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    file: Mapped[MediaFile] = relationship(lazy="selectin")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    __table_args__ = (
        sa.CheckConstraint("status IN ('pending', 'cancelled')", name="ck_processing_jobs_status"),
        sa.Index("ix_processing_jobs_order", "status", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    source_id: Mapped[UUID] = mapped_column(sa.ForeignKey("sources.id", ondelete="RESTRICT"), unique=True)
    status: Mapped[str] = mapped_column(sa.Text, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
