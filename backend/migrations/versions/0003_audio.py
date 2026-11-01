"""Manual sequential audio engine and immutable transcript history."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_audio"
down_revision = "0002_library"
branch_labels = None
depends_on = None


def identity():
    return sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()"))


def upgrade():
    op.drop_constraint("ck_processing_jobs_status", "processing_jobs")
    op.create_check_constraint("ck_processing_jobs_status", "processing_jobs", "status IN ('pending', 'cancelled', 'running', 'completed', 'failed', 'stopped', 'unavailable')")
    op.add_column("processing_jobs", sa.Column("run_id", sa.Uuid()))
    op.add_column("processing_jobs", sa.Column("error_message", sa.Text()))
    op.create_table("engine_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("state", sa.Text(), nullable=False, server_default="stopped"),
        sa.Column("run_id", sa.Uuid()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("id = 1", name="ck_engine_singleton"),
        sa.CheckConstraint("state IN ('stopped', 'running', 'pause_requested', 'paused', 'stop_requested')", name="ck_engine_state"))
    op.execute("INSERT INTO engine_state(id) VALUES (1)")
    op.create_table("processing_attempts", identity(),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("processing_jobs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.CheckConstraint("status IN ('running', 'completed', 'failed', 'stopped', 'unavailable')", name="ck_attempt_status"))
    op.create_index("ix_processing_attempts_job_id", "processing_attempts", ["job_id"])
    op.create_table("transcripts", identity(),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("asset_id", sa.Uuid(), sa.ForeignKey("media_assets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), sa.ForeignKey("processing_attempts.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("language", sa.Text()),
        sa.Column("duration_ms", sa.BigInteger(), nullable=False),
        sa.Column("provenance", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("source_id", "version", name="uq_transcript_version"),
        sa.CheckConstraint("version > 0 AND duration_ms >= 0", name="ck_transcript_numbers"),
        sa.CheckConstraint("outcome IN ('speech', 'no_speech', 'no_audio')", name="ck_transcript_outcome"))
    op.create_index("ix_transcripts_source_id", "transcripts", ["source_id"])
    op.create_table("transcript_segments", identity(),
        sa.Column("transcript_id", sa.Uuid(), sa.ForeignKey("transcripts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.BigInteger(), nullable=False),
        sa.Column("end_ms", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.UniqueConstraint("transcript_id", "ordinal", name="uq_segment_ordinal"),
        sa.CheckConstraint("ordinal >= 0 AND start_ms >= 0 AND end_ms > start_ms", name="ck_segment_interval"))
    op.create_index("ix_transcript_segments_transcript_id", "transcript_segments", ["transcript_id"])


def downgrade():
    raise RuntimeError("El historial de transcripciones se conserva; no hay downgrade destructivo.")
