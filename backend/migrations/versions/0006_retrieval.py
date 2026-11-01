"""Local evidence chunks, separate embedding profiles and explicit retrieval jobs."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision='0006_retrieval'
down_revision='0005_audiovisual'
branch_labels=None
depends_on=None

class EmbeddingVector(sa.types.UserDefinedType):
    def get_col_spec(self, **kw): return 'public.vector(1024)'

def ident(): return sa.Column('id',sa.Uuid(),primary_key=True,server_default=sa.text('gen_random_uuid()'))
def upgrade():
    if not op.get_bind().scalar(sa.text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")):
        raise RuntimeError('Falta habilitar pgvector en la base ReelMind antes de migrar.')
    op.create_unique_constraint('uq_transcript_id_source','transcripts',['id','source_id'])
    op.create_unique_constraint('uq_av_id_source','audiovisual_analyses',['id','source_id'])
    op.create_table('embedding_profiles',sa.Column('id',sa.String(64),primary_key=True),
        sa.Column('model',sa.Text,nullable=False),sa.Column('digest',sa.Text,nullable=False),
        sa.Column('dimensions',sa.Integer,nullable=False),sa.Column('configuration',JSONB,nullable=False),
        sa.CheckConstraint('dimensions = 1024',name='ck_embedding_dimensions'))
    op.create_table('content_chunks',ident(),
        sa.Column('source_id',sa.Uuid(),sa.ForeignKey('sources.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('analysis_id',sa.Uuid()),sa.Column('transcript_id',sa.Uuid()),
        sa.Column('origin_key',sa.Text,unique=True,nullable=False),sa.Column('ordinal',sa.Integer,nullable=False),
        sa.Column('content',sa.Text,nullable=False),sa.Column('content_sha256',sa.String(64),nullable=False),
        sa.Column('start_ms',sa.BigInteger),sa.Column('end_ms',sa.BigInteger),sa.Column('time_ms',sa.BigInteger),
        sa.Column('origin',JSONB,nullable=False),
        sa.CheckConstraint('(analysis_id IS NULL) <> (transcript_id IS NULL)',name='ck_chunk_origin'),
        sa.CheckConstraint('ordinal >= 0 AND length(content) BETWEEN 1 AND 1200',name='ck_chunk_content'),
        sa.CheckConstraint('(start_ms IS NULL AND end_ms IS NULL) OR (start_ms IS NOT NULL AND end_ms IS NOT NULL AND start_ms >= 0 AND end_ms > start_ms)',name='ck_chunk_interval'),
        sa.CheckConstraint('time_ms IS NULL OR time_ms >= 0',name='ck_chunk_point'),
        sa.ForeignKeyConstraint(['analysis_id','source_id'],['audiovisual_analyses.id','audiovisual_analyses.source_id'],name='fk_chunk_analysis_source',ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['transcript_id','source_id'],['transcripts.id','transcripts.source_id'],name='fk_chunk_transcript_source',ondelete='RESTRICT'))
    op.create_index('ix_content_chunks_source_id','content_chunks',['source_id'])
    op.create_table('chunk_embeddings',
        sa.Column('chunk_id',sa.Uuid(),sa.ForeignKey('content_chunks.id',ondelete='RESTRICT'),primary_key=True),
        sa.Column('profile_id',sa.String(64),sa.ForeignKey('embedding_profiles.id',ondelete='RESTRICT'),primary_key=True),
        sa.Column('embedding',EmbeddingVector(),nullable=False))
    op.create_table('chat_sessions',ident(),sa.Column('title',sa.String(120),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_table('retrieval_tasks',ident(),sa.Column('action',sa.Text,nullable=False),sa.Column('status',sa.Text,nullable=False),
        sa.Column('query',sa.String(800),nullable=False,server_default=''),
        sa.Column('session_id',sa.Uuid(),sa.ForeignKey('chat_sessions.id',ondelete='RESTRICT')),
        sa.Column('profile_id',sa.String(64),nullable=False),sa.Column('result',JSONB,nullable=False,server_default='{}'),
        sa.Column('error_message',sa.Text),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.Column('finished_at',sa.DateTime(timezone=True)),
        sa.CheckConstraint("action IN ('index','search','chat')",name='ck_retrieval_action'),
        sa.CheckConstraint("status IN ('running','stop_requested','completed','failed','stopped')",name='ck_retrieval_state'))

def downgrade(): raise RuntimeError('No se elimina automáticamente historial de índice o chat.')
