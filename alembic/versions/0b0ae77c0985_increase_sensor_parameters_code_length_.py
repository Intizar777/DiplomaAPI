"""increase sensor_parameters code length to 50

Revision ID: 0b0ae77c0985
Revises: 4a3168777436
Create Date: 2026-05-14 17:24:40.362950+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b0ae77c0985'
down_revision = '4a3168777436'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('sensor_parameters', 'code',
               existing_type=sa.String(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('sensor_parameters', 'code',
               existing_type=sa.String(length=50),
               type_=sa.String(length=20),
               existing_nullable=False)
