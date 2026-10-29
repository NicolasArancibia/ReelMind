"""Initial persisted sources. No workers, downloads or analysis are started."""
from alembic import op
import sqlalchemy as sa

revision = "0001_sources"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("original_url", sa.Text()),
        sa.Column("canonical_url", sa.Text()),
        sa.Column("title", sa.String(240)),
        sa.Column("author", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("platform IN ('instagram', 'youtube', 'tiktok', 'local', 'other')", name="ck_sources_platform"),
        sa.CheckConstraint("source_type IN ('url', 'file')", name="ck_sources_type"),
        sa.CheckConstraint("source_type <> 'url' OR (original_url IS NOT NULL AND btrim(original_url) <> '')", name="ck_sources_url_required"),
        sa.CheckConstraint("status IN ('pending', 'ready', 'needs_input', 'failed')", name="ck_sources_status"),
    )
    op.create_index("uq_sources_canonical_url", "sources", ["canonical_url"], unique=True, postgresql_where=sa.text("canonical_url IS NOT NULL"))
    op.create_index("ix_sources_status_created_at", "sources", ["status", "created_at"])
    op.create_index("ix_sources_platform", "sources", ["platform"])


def downgrade():
    raise RuntimeError("Esta revisión contiene fuentes personales. Restaurar un respaldo verificado; no se admite borrado automático.")
