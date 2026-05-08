"""Remove denormalized warehouse_code column from inventory_snapshots

Revision ID: 004_remove_denormalized_warehouse_code
Revises: 003_remove_denorm_sensors
Create Date: 2026-05-08 12:15:00.000000+00:00

After introducing warehouse_id FK, remove the denormalized warehouse_code.
Warehouse information is now accessed through the warehouse_id foreign key.
"""
from alembic import op
import sqlalchemy as sa


revision = '004_remove_denorm_warehouse'
down_revision = '003_remove_denorm_sensors'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update indices to use warehouse_id instead of warehouse_code
    op.drop_index('idx_inventory_product_warehouse', table_name='inventory_snapshots', if_exists=True)
    op.drop_index('idx_inventory_date_warehouse', table_name='inventory_snapshots', if_exists=True)

    # Recreate indices with warehouse_id
    op.create_index(
        'idx_inventory_product_warehouse',
        'inventory_snapshots',
        ['product_id', 'warehouse_id']
    )
    op.create_index(
        'idx_inventory_date_warehouse',
        'inventory_snapshots',
        ['snapshot_date', 'warehouse_id']
    )

    # Drop warehouse_code column
    op.drop_column('inventory_snapshots', 'warehouse_code')


def downgrade() -> None:
    # Restore warehouse_code column (nullable)
    op.add_column('inventory_snapshots', sa.Column('warehouse_code', sa.String(length=50), nullable=True))

    # Restore indices
    op.drop_index('idx_inventory_date_warehouse', table_name='inventory_snapshots', if_exists=True)
    op.drop_index('idx_inventory_product_warehouse', table_name='inventory_snapshots', if_exists=True)

    op.create_index(
        'idx_inventory_product_warehouse',
        'inventory_snapshots',
        ['product_id', 'warehouse_code']
    )
    op.create_index(
        'idx_inventory_date_warehouse',
        'inventory_snapshots',
        ['snapshot_date', 'warehouse_code']
    )
