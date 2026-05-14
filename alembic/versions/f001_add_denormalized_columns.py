"""add_denormalized_columns_for_analytics

Revision ID: f001
Revises: e42439396426
Create Date: 2026-05-14 12:00:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f001'
down_revision = 'c993b27cc996'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add denormalized columns to inventory_snapshots
    op.add_column('inventory_snapshots', sa.Column('warehouse_name', sa.String(150), nullable=True))
    op.add_column('inventory_snapshots', sa.Column('warehouse_code', sa.String(20), nullable=True, index=True))

    # Add denormalized columns to sensors
    op.add_column('sensors', sa.Column('line_name', sa.String(255), nullable=True))
    op.add_column('sensors', sa.Column('parameter_name', sa.String(100), nullable=True))
    op.add_column('sensors', sa.Column('parameter_unit', sa.String(20), nullable=True))

    # Add denormalized columns to aggregated_kpi
    op.add_column('aggregated_kpi', sa.Column('production_line_name', sa.String(255), nullable=True))

    # Add denormalized columns to production_output
    op.add_column('production_output', sa.Column('production_line_id', sa.UUID, nullable=True, index=True))
    op.add_column('production_output', sa.Column('production_line_name', sa.String(255), nullable=True))


def downgrade() -> None:
    # Remove denormalized columns from production_output
    op.drop_column('production_output', 'production_line_name')
    op.drop_column('production_output', 'production_line_id')

    # Remove denormalized columns from aggregated_kpi
    op.drop_column('aggregated_kpi', 'production_line_name')

    # Remove denormalized columns from sensors
    op.drop_column('sensors', 'parameter_unit')
    op.drop_column('sensors', 'parameter_name')
    op.drop_column('sensors', 'line_name')

    # Remove denormalized columns from inventory_snapshots
    op.drop_column('inventory_snapshots', 'warehouse_code')
    op.drop_column('inventory_snapshots', 'warehouse_name')
