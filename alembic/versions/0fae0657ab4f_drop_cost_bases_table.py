"""drop_cost_bases_table

Revision ID: 0fae0657ab4f
Revises: 88817dbdd9e5
Create Date: 2026-05-14 12:39:30.959375+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0fae0657ab4f'
down_revision = '88817dbdd9e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('idx_cost_base_period', 'cost_bases')
    op.drop_index('idx_cost_base_product_period', 'cost_bases')
    op.drop_index('ix_cost_bases_period_from', 'cost_bases')
    op.drop_index('ix_cost_bases_product_id', 'cost_bases')
    op.drop_table('cost_bases')


def downgrade() -> None:
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
