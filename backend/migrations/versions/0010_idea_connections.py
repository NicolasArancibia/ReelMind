"""Pin relationship endpoints to immutable personal-note revisions when selected."""
from alembic import op
import sqlalchemy as sa
revision='0010_idea_connections'
down_revision='0009_personal_library'
branch_labels=None
depends_on=None

def upgrade():
    for side in ('from','to'):
        op.add_column('relation_revisions',sa.Column(side+'_note_id',sa.Uuid()))
        op.add_column('relation_revisions',sa.Column(side+'_note_version',sa.Integer()))
        op.create_foreign_key('fk_relation_'+side+'_note','relation_revisions','note_revisions',[side+'_note_id',side+'_note_version',side+'_source_id'],['id','version','source_id'],ondelete='RESTRICT')
        op.create_check_constraint('ck_relation_'+side+'_note','relation_revisions',f'({side}_note_id IS NULL) = ({side}_note_version IS NULL)')
    op.drop_constraint('ck_relation_identity','relation_revisions',type_='check')
    op.create_check_constraint('ck_relation_identity','relation_revisions',"version > 0 AND (from_source_id <> to_source_id OR coalesce(from_note_id::text, '') <> coalesce(to_note_id::text, ''))")

def downgrade():raise RuntimeError('No se eliminan referencias a ideas automáticamente.')
