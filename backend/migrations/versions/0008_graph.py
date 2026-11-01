"""Append-only source relationships with manual evidence."""
from alembic import op
import sqlalchemy as sa
revision='0008_graph'
down_revision='0007_projects'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('relation_revisions',
        sa.Column('id',sa.Uuid(),primary_key=True),sa.Column('version',sa.Integer(),primary_key=True),
        sa.Column('project_id',sa.Uuid(),sa.ForeignKey('projects.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('from_source_id',sa.Uuid(),sa.ForeignKey('sources.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('to_source_id',sa.Uuid(),sa.ForeignKey('sources.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('label',sa.String(120),nullable=False),sa.Column('evidence',sa.String(2000),nullable=False),
        sa.Column('review_status',sa.String(20),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.CheckConstraint('version > 0 AND from_source_id <> to_source_id',name='ck_relation_identity'),
        sa.CheckConstraint('length(btrim(label)) > 0 AND length(btrim(evidence)) > 0',name='ck_relation_evidence'),
        sa.CheckConstraint("review_status IN ('proposed','accepted','rejected')",name='ck_relation_review'))
    op.create_index('ix_relation_revisions_project_id','relation_revisions',['project_id'])

def downgrade(): raise RuntimeError('No se elimina historial de relaciones automáticamente.')
