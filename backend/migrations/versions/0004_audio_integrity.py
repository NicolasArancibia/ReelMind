"""Enforce transcript asset provenance at the database boundary."""
from alembic import op

revision = "0004_audio_integrity"
down_revision = "0003_audio"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("uq_media_assets_id_source", "media_assets", ["id", "source_id"])
    op.create_foreign_key("fk_transcript_asset_source", "transcripts", "media_assets",
                          ["asset_id", "source_id"], ["id", "source_id"], ondelete="RESTRICT")


def downgrade():
    raise RuntimeError("No se retira la garantía de procedencia automáticamente.")
