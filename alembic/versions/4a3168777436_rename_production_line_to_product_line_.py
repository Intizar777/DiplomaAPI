"""rename_production_line_to_product_line_id_in_aggregated_kpi

Revision ID: 4a3168777436
Revises: d5cefd594a89
Create Date: 2026-05-14 12:44:52.316957+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a3168777436'
down_revision = 'd5cefd594a89'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint('uix_kpi_period_line', 'aggregated_kpi', type_='unique')
    op.drop_index('ix_aggregated_kpi_production_line', table_name='aggregated_kpi')
    op.alter_column('aggregated_kpi', 'production_line', new_column_name='product_line_id')
    op.create_index('ix_aggregated_kpi_product_line_id', 'aggregated_kpi', ['product_line_id'], unique=False)
    op.create_unique_constraint('uix_kpi_period_line', 'aggregated_kpi',
                               ['period_from', 'period_to', 'product_line_id'])


def downgrade() -> None:
    op.drop_constraint('uix_kpi_period_line', 'aggregated_kpi', type_='unique')
    op.drop_index('ix_aggregated_kpi_product_line_id', table_name='aggregated_kpi')
    op.alter_column('aggregated_kpi', 'product_line_id', new_column_name='production_line')
    op.create_index('ix_aggregated_kpi_production_line', 'aggregated_kpi', ['production_line'], unique=False)
    op.create_unique_constraint('uix_kpi_period_line', 'aggregated_kpi',
                               ['period_from', 'period_to', 'production_line'])
