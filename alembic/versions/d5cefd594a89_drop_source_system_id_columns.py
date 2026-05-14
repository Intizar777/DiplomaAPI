"""drop_source_system_id_columns

Revision ID: d5cefd594a89
Revises: 0fae0657ab4f
Create Date: 2026-05-14 12:40:26.578427+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5cefd594a89'
down_revision = '0fae0657ab4f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('ix_units_of_measure_source_system_id', 'units_of_measure', if_exists=True)
    op.drop_column('units_of_measure', 'source_system_id')

    op.drop_index('ix_warehouses_source_system_id', 'warehouses', if_exists=True)
    op.drop_column('warehouses', 'source_system_id')

    op.drop_index('ix_customers_source_system_id', 'customers', if_exists=True)
    op.drop_column('customers', 'source_system_id')


def downgrade() -> None:
    op.add_column('customers', sa.Column('source_system_id', sa.String(100), nullable=True))
    op.create_index('ix_customers_source_system_id', 'customers', ['source_system_id'], unique=True)

    op.add_column('warehouses', sa.Column('source_system_id', sa.String(100), nullable=True))
    op.create_index('ix_warehouses_source_system_id', 'warehouses', ['source_system_id'], unique=True)

    op.add_column('units_of_measure', sa.Column('source_system_id', sa.String(100), nullable=True))
    op.create_index('ix_units_of_measure_source_system_id', 'units_of_measure', ['source_system_id'], unique=True)
