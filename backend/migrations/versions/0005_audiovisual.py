"""Versioned audiovisual evidence with same-source transcript provenance."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0005_audiovisual'
down_revision = '0004_audio_integrity'
branch_labels = None
depends_on = None

def upgrade():
    op.create_unique_constraint('uq_transcript_id_source_asset', 'transcripts', ['id', 'source_id', 'asset_id'])
    op.create_table('audiovisual_analyses',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_id', sa.Uuid(), sa.ForeignKey('sources.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('asset_id', sa.Uuid(), sa.ForeignKey('media_assets.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('transcript_id', sa.Uuid(), sa.ForeignKey('transcripts.id', ondelete='RESTRICT'), nullable=False, unique=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('payload', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('source_id', 'version', name='uq_av_version'),
        sa.CheckConstraint('version > 0', name='ck_av_version'),
        sa.ForeignKeyConstraint(['transcript_id', 'source_id', 'asset_id'],
            ['transcripts.id', 'transcripts.source_id', 'transcripts.asset_id'], name='fk_av_transcript_source_asset', ondelete='RESTRICT'))
    op.create_index('ix_audiovisual_analyses_source_id', 'audiovisual_analyses', ['source_id'])

def downgrade():
    raise RuntimeError('No se elimina el historial audiovisual automáticamente.')
