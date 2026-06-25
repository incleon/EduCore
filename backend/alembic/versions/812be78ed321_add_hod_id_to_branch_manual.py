"""Add hod_id to branch manual
Revision ID: 812be78ed321
Revises: f437010c7643
Create Date: 2026-06-29 23:36:41.076517
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '812be78ed321'
down_revision = 'f437010c7643'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('branches', sa.Column('hod_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_branches_hod_id', 'branches', 'teachers', ['hod_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_branches_hod_id', 'branches', type_='foreignkey')
    op.drop_column('branches', 'hod_id')
