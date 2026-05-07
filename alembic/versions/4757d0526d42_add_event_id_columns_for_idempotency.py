"""add_event_id_columns_for_idempotency

Revision ID: 4757d0526d42
Revises: 1122e8e59f9b
Create Date: 2026-05-07 12:43:14.874452+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4757d0526d42'
down_revision = '1122e8e59f9b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add event_id column to products
    op.add_column('products', sa.Column('event_id', sa.UUID(), nullable=True))
    op.create_index(
        op.f('ix_products_event_id'),
        'products',
        ['event_id'],
        unique=True,
        postgresql_where=sa.text('event_id IS NOT NULL')
    )

    # Add event_id column to order_snapshots
    op.add_column('order_snapshots', sa.Column('event_id', sa.UUID(), nullable=True))
    op.create_index(
        op.f('ix_order_snapshots_event_id'),
        'order_snapshots',
        ['event_id'],
        unique=True,
        postgresql_where=sa.text('event_id IS NOT NULL')
    )

    # Add event_id column to production_output
    op.add_column('production_output', sa.Column('event_id', sa.UUID(), nullable=True))
    op.create_index(
        op.f('ix_production_output_event_id'),
        'production_output',
        ['event_id'],
        unique=True,
        postgresql_where=sa.text('event_id IS NOT NULL')
    )

    # Add event_id column to sale_records
    op.add_column('sale_records', sa.Column('event_id', sa.UUID(), nullable=True))
    op.create_index(
        op.f('ix_sale_records_event_id'),
        'sale_records',
        ['event_id'],
        unique=True,
        postgresql_where=sa.text('event_id IS NOT NULL')
    )

    # Add event_id column to inventory_snapshots
    op.add_column('inventory_snapshots', sa.Column('event_id', sa.UUID(), nullable=True))
    op.create_index(
        op.f('ix_inventory_snapshots_event_id'),
        'inventory_snapshots',
        ['event_id'],
        unique=True,
        postgresql_where=sa.text('event_id IS NOT NULL')
    )

    # Add event_id column to quality_results
    op.add_column('quality_results', sa.Column('event_id', sa.UUID(), nullable=True))
    op.create_index(
        op.f('ix_quality_results_event_id'),
        'quality_results',
        ['event_id'],
        unique=True,
        postgresql_where=sa.text('event_id IS NOT NULL')
    )


def downgrade() -> None:
    # Drop indices
    op.drop_index('ix_quality_results_event_id', table_name='quality_results')
    op.drop_index('ix_inventory_snapshots_event_id', table_name='inventory_snapshots')
    op.drop_index('ix_sale_records_event_id', table_name='sale_records')
    op.drop_index('ix_production_output_event_id', table_name='production_output')
    op.drop_index('ix_order_snapshots_event_id', table_name='order_snapshots')
    op.drop_index('ix_products_event_id', table_name='products')

    # Drop columns
    op.drop_column('quality_results', 'event_id')
    op.drop_column('inventory_snapshots', 'event_id')
    op.drop_column('sale_records', 'event_id')
    op.drop_column('production_output', 'event_id')
    op.drop_column('order_snapshots', 'event_id')
    op.drop_column('products', 'event_id')
