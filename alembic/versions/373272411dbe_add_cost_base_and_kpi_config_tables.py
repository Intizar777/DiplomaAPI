"""add_cost_base_and_kpi_config_tables

Revision ID: 373272411dbe
Revises: e42439396426
Create Date: 2026-05-12 07:18:37.158339+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '373272411dbe'
down_revision = 'e42439396426'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create cost_bases table
    op.create_table(
        'cost_bases',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('raw_material_cost', sa.DECIMAL(precision=15, scale=4), nullable=False),
        sa.Column('labor_cost_per_hour', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('depreciation_monthly', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('period_from', sa.Date, nullable=False),
        sa.Column('period_to', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cost_bases_product_id', 'cost_bases', ['product_id'])
    op.create_index('ix_cost_bases_period_from', 'cost_bases', ['period_from'])
    op.create_index('idx_cost_base_product_period', 'cost_bases', ['product_id', 'period_from'])
    op.create_index('idx_cost_base_period', 'cost_bases', ['period_from', 'period_to'])

    # Create kpi_configs table
    op.create_table(
        'kpi_configs',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.DECIMAL(precision=20, scale=4), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )
    op.create_index('idx_kpi_config_key', 'kpi_configs', ['key'])


def downgrade() -> None:
    # Drop kpi_configs table
    op.drop_index('idx_kpi_config_key', 'kpi_configs')
    op.drop_table('kpi_configs')

    # Drop cost_bases table
    op.drop_index('idx_cost_base_period', 'cost_bases')
    op.drop_index('idx_cost_base_product_period', 'cost_bases')
    op.drop_index('ix_cost_bases_period_from', 'cost_bases')
    op.drop_index('ix_cost_bases_product_id', 'cost_bases')
    op.drop_table('cost_bases')
