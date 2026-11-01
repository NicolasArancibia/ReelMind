"""Versioned personal notes, recoverable organization and scoped conversations."""
from alembic import op
import sqlalchemy as sa
revision='0009_personal_library'
down_revision='0008_graph'
branch_labels=None
depends_on=None

def upgrade():
    for table in ('projects','chat_sessions'):
        op.add_column(table,sa.Column('archived_at',sa.DateTime(timezone=True)))
    op.add_column('chat_sessions',sa.Column('project_id',sa.Uuid(),sa.ForeignKey('projects.id',ondelete='RESTRICT')))
    op.add_column('sources',sa.Column('favorite',sa.Boolean(),nullable=False,server_default=sa.false()))
    op.add_column('sources',sa.Column('summary',sa.Text()))
    op.create_unique_constraint('uq_chunk_id_source','content_chunks',['id','source_id'])
    op.create_table('note_revisions',sa.Column('id',sa.Uuid(),primary_key=True),sa.Column('version',sa.Integer(),primary_key=True),
        sa.Column('source_id',sa.Uuid(),sa.ForeignKey('sources.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('content',sa.String(8000),nullable=False),sa.Column('quote_chunk_id',sa.Uuid()),sa.Column('quote_text',sa.Text()),
        sa.Column('start_ms',sa.BigInteger()),sa.Column('end_ms',sa.BigInteger()),
        sa.Column('favorite',sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column('archived',sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.UniqueConstraint('id','version','source_id',name='uq_note_version_source'),
        sa.ForeignKeyConstraint(['quote_chunk_id','source_id'],['content_chunks.id','content_chunks.source_id'],ondelete='RESTRICT',name='fk_note_quote_source'),
        sa.CheckConstraint('version > 0 AND length(btrim(content)) > 0',name='ck_note_content'),
        sa.CheckConstraint('(start_ms IS NULL AND end_ms IS NULL) OR (start_ms IS NOT NULL AND start_ms >= 0 AND end_ms IS NOT NULL AND end_ms > start_ms)',name='ck_note_interval'))
    op.create_index('ix_note_revisions_source_id','note_revisions',['source_id'])
    op.add_column('content_chunks',sa.Column('note_id',sa.Uuid()))
    op.add_column('content_chunks',sa.Column('note_version',sa.Integer()))
    op.drop_constraint('ck_chunk_origin','content_chunks',type_='check')
    op.create_check_constraint('ck_chunk_origin','content_chunks','num_nonnulls(analysis_id,transcript_id,note_id) = 1 AND ((note_id IS NULL) = (note_version IS NULL))')
    op.create_foreign_key('fk_chunk_note_source','content_chunks','note_revisions',['note_id','note_version','source_id'],['id','version','source_id'],ondelete='RESTRICT')

def downgrade(): raise RuntimeError('No se eliminan apuntes ni organización automáticamente.')
