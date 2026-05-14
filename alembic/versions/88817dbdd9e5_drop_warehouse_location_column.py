"""drop_warehouse_location_column

Revision ID: 88817dbdd9e5
Revises: f001
Create Date: 2026-05-14 12:38:03.642106+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88817dbdd9e5'
down_revision = 'f001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('warehouses', 'location')


def downgrade() -> None:
    op.add_column('warehouses', sa.Column('location', sa.String(200), nullable=False, server_default='Unknown'))
    op.alter_column('warehouses', 'location', server_default=None)
