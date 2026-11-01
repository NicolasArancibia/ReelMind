"""Local projects and explicit source membership."""
from alembic import op
import sqlalchemy as sa
revision='0007_projects'
down_revision='0006_retrieval'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('projects',sa.Column('id',sa.Uuid(),primary_key=True,server_default=sa.text('gen_random_uuid()')),
        sa.Column('name',sa.String(120),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.CheckConstraint('length(btrim(name)) > 0',name='ck_project_name'))
    op.create_table('project_sources',sa.Column('project_id',sa.Uuid(),sa.ForeignKey('projects.id',ondelete='RESTRICT'),primary_key=True),
        sa.Column('source_id',sa.Uuid(),sa.ForeignKey('sources.id',ondelete='RESTRICT'),primary_key=True),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))
    op.create_index('ix_project_sources_source_id','project_sources',['source_id'])

def downgrade(): raise RuntimeError('No se eliminan proyectos ni asociaciones automáticamente.')
