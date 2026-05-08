"""Add foreign keys to existing tables (3NF normalization)

Revision ID: 002_add_foreign_keys_to_existing_tables
Revises: 001_ref_tables_3nf
Create Date: 2026-05-08 12:05:00.000000+00:00

Changes to existing tables:
- products: add unit_of_measure_id FK
- inventory_snapshots: change warehouse_code to warehouse_id FK
- sensor_readings: change to sensor_id FK (remove device_id, parameter_name, unit)
- sale_records: add customer_id FK
- quality_results: add quality_spec_id FK
"""
from alembic import op
import sqlalchemy as sa


revision = '002_add_fk_existing'
down_revision = '001_ref_tables_3nf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. products: add unit_of_measure_id FK
    op.add_column('products', sa.Column('unit_of_measure_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_products_unit_of_measure_id',
        'products', 'units_of_measure',
        ['unit_of_measure_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_products_unit_of_measure_id', 'products', ['unit_of_measure_id'])

    # 2. inventory_snapshots: add warehouse_id FK
    op.add_column('inventory_snapshots', sa.Column('warehouse_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_inventory_snapshots_warehouse_id',
        'inventory_snapshots', 'warehouses',
        ['warehouse_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_inventory_snapshots_warehouse_id', 'inventory_snapshots', ['warehouse_id'])

    # 3. sale_records: add customer_id FK
    op.add_column('sale_records', sa.Column('customer_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_sale_records_customer_id',
        'sale_records', 'customers',
        ['customer_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_sale_records_customer_id', 'sale_records', ['customer_id'])

    # 4. quality_results: add quality_spec_id FK
    op.add_column('quality_results', sa.Column('quality_spec_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_quality_results_quality_spec_id',
        'quality_results', 'quality_specs',
        ['quality_spec_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_quality_results_quality_spec_id', 'quality_results', ['quality_spec_id'])

    # 5. sensor_readings: add sensor_id FK
    op.add_column('sensor_readings', sa.Column('sensor_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_sensor_readings_sensor_id',
        'sensor_readings', 'sensors',
        ['sensor_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index('ix_sensor_readings_sensor_id', 'sensor_readings', ['sensor_id'])


def downgrade() -> None:
    # Drop indices and FKs (in reverse order)

    # sensor_readings
    op.drop_index('ix_sensor_readings_sensor_id', table_name='sensor_readings')
    op.drop_constraint('fk_sensor_readings_sensor_id', 'sensor_readings', type_='foreignkey')
    op.drop_column('sensor_readings', 'sensor_id')

    # quality_results
    op.drop_index('ix_quality_results_quality_spec_id', table_name='quality_results')
    op.drop_constraint('fk_quality_results_quality_spec_id', 'quality_results', type_='foreignkey')
    op.drop_column('quality_results', 'quality_spec_id')

    # sale_records
    op.drop_index('ix_sale_records_customer_id', table_name='sale_records')
    op.drop_constraint('fk_sale_records_customer_id', 'sale_records', type_='foreignkey')
    op.drop_column('sale_records', 'customer_id')

    # inventory_snapshots
    op.drop_index('ix_inventory_snapshots_warehouse_id', table_name='inventory_snapshots')
    op.drop_constraint('fk_inventory_snapshots_warehouse_id', 'inventory_snapshots', type_='foreignkey')
    op.drop_column('inventory_snapshots', 'warehouse_id')

    # products
    op.drop_index('ix_products_unit_of_measure_id', table_name='products')
    op.drop_constraint('fk_products_unit_of_measure_id', 'products', type_='foreignkey')
    op.drop_column('products', 'unit_of_measure_id')
