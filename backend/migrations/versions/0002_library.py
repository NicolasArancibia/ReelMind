"""Local media, flat organization and a dormant persistent queue."""
from alembic import op
import sqlalchemy as sa

revision = "0002_library"
down_revision = "0001_sources"
branch_labels = None
depends_on = None


def identity():
    return sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()"))


def upgrade():
    for table in ("tags", "categories"):
        op.create_table(table, identity(),
            sa.Column("name", sa.String(60), nullable=False),
            sa.Column("normalized_name", sa.Text(), nullable=False, unique=True),
            sa.CheckConstraint("btrim(name) <> ''", name=f"ck_{table}_name"))
    for table, target, column in (("source_tags", "tags", "tag_id"), ("source_categories", "categories", "category_id")):
        op.create_table(table,
            sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), primary_key=True),
            sa.Column(column, sa.Uuid(), sa.ForeignKey(f"{target}.id", ondelete="RESTRICT"), primary_key=True))
        op.create_index(f"ix_{table}_{'tag' if target == 'tags' else 'category'}", table, [column])
    op.create_table("media_files", identity(),
        sa.Column("checksum", sa.String(64), nullable=False, unique=True),
        sa.Column("local_path", sa.Text(), nullable=False, unique=True),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("size_bytes > 0", name="ck_media_files_size"))
    op.create_table("media_assets", identity(),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("file_id", sa.Uuid(), sa.ForeignKey("media_files.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("original_name", sa.String(240), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_id", "file_id", name="uq_media_assets_source_file"))
    op.create_index("ix_media_assets_source_id", "media_assets", ["source_id"])
    op.create_index("ix_media_assets_file_id", "media_assets", ["file_id"])
    op.create_table("processing_jobs", identity(),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("status", sa.Text(), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'cancelled')", name="ck_processing_jobs_status"))
    op.create_index("ix_processing_jobs_order", "processing_jobs", ["status", "created_at"])
    op.execute("INSERT INTO processing_jobs (source_id, created_at) SELECT id, created_at FROM sources")


def downgrade():
    raise RuntimeError("La biblioteca contiene asociaciones y medios personales. No se admite borrado automático.")
