"""Add versioning support to timetables
Revision ID: cc9cb668516c
Revises: 812be78ed321
Create Date: 2026-06-30 07:27:25.373883
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc9cb668516c'
down_revision = '812be78ed321'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('timetable_versions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'))
        batch_op.drop_constraint('uq_timetable_scope', type_='unique')
        batch_op.create_unique_constraint('uq_timetable_scope_version', ['course_id', 'branch_scope_key', 'semester', 'section_scope_key', 'version_number'])


def downgrade() -> None:
    with op.batch_alter_table('timetable_versions', schema=None) as batch_op:
        batch_op.drop_constraint('uq_timetable_scope_version', type_='unique')
        batch_op.create_unique_constraint('uq_timetable_scope', ['course_id', 'branch_scope_key', 'semester', 'section_scope_key'])
        batch_op.drop_column('version_number')
