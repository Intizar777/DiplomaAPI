"""add cost column to sale_records

Revision ID: 2e566eb26ef2
Revises: 373272411dbe
Create Date: 2026-05-12 08:27:45.729980+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e566eb26ef2'
down_revision = '373272411dbe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sale_records', sa.Column('cost', sa.DECIMAL(precision=15, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('sale_records', 'cost')
