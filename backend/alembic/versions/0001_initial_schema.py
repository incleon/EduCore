"""Initial schema revision

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-06-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a baseline migration stub. Use `alembic revision --autogenerate -m "Initial schema"`
    # to generate the full schema from current models, then replace this file with generated operations.
    pass


def downgrade() -> None:
    pass
