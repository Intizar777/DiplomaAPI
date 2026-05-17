"""add group_id to aggregated_sales for product grouping

Revision ID: f002
Revises: d71274f19362
Create Date: 2026-05-17 00:00:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f002'
down_revision = 'd71274f19362'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('aggregated_sales', sa.Column('group_id', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('aggregated_sales', 'group_id')
