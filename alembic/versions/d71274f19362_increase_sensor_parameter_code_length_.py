"""increase sensor_parameter code length to 50

Revision ID: d71274f19362
Revises: 0b0ae77c0985
Create Date: 2026-05-14 17:38:06.373778+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd71274f19362'
down_revision = '0b0ae77c0985'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('sensor_parameters', 'code',
               existing_type=sa.String(20),
               type_=sa.String(50),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('sensor_parameters', 'code',
               existing_type=sa.String(50),
               type_=sa.String(20),
               existing_nullable=False)
