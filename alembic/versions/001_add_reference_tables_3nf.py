"""Add reference tables for 3NF normalization

Revision ID: 001_add_reference_tables_3nf
Revises: 4757d0526d42
Create Date: 2026-05-08 12:00:00.000000+00:00

New tables:
- units_of_measure: UnitOfMeasure references (code, name)
- warehouses: Warehouse references (code, name, location, capacity)
- sensor_parameters: SensorParameter references (code, name, unit)
- sensors: Sensor references (device_id, production_line_id, sensor_parameter_id)
- customers: Customer references (code, name, region)
- quality_specs: QualitySpec references (product_id, parameter_name, limits)
"""
from alembic import op
import sqlalchemy as sa


revision = '001_add_reference_tables_3nf'
down_revision = '4757d0526d42'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create units_of_measure table
    op.create_table(
        'units_of_measure',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('source_system_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_units_of_measure_code'),
        sa.UniqueConstraint('source_system_id', name='uq_units_of_measure_source_system_id'),
    )
    op.create_index('ix_units_of_measure_code', 'units_of_measure', ['code'], unique=True)
    op.create_index('ix_units_of_measure_source_system_id', 'units_of_measure', ['source_system_id'], unique=True)

    # Create warehouses table
    op.create_table(
        'warehouses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('capacity', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('source_system_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_warehouses_code'),
        sa.UniqueConstraint('source_system_id', name='uq_warehouses_source_system_id'),
    )
    op.create_index('ix_warehouses_code', 'warehouses', ['code'], unique=True)
    op.create_index('ix_warehouses_is_active', 'warehouses', ['is_active'])
    op.create_index('ix_warehouses_source_system_id', 'warehouses', ['source_system_id'], unique=True)

    # Create sensor_parameters table
    op.create_table(
        'sensor_parameters',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_sensor_parameters_code'),
    )
    op.create_index('ix_sensor_parameters_code', 'sensor_parameters', ['code'], unique=True)
    op.create_index('ix_sensor_parameters_is_active', 'sensor_parameters', ['is_active'])

    # Create sensors table
    op.create_table(
        'sensors',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('device_id', sa.String(length=50), nullable=False),
        sa.Column('production_line_id', sa.UUID(), nullable=False),
        sa.Column('sensor_parameter_id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sensor_parameter_id'], ['sensor_parameters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('device_id', name='uq_sensors_device_id'),
    )
    op.create_index('ix_sensors_device_id', 'sensors', ['device_id'], unique=True)
    op.create_index('ix_sensors_production_line_id', 'sensors', ['production_line_id'])
    op.create_index('ix_sensors_sensor_parameter_id', 'sensors', ['sensor_parameter_id'])
    op.create_index('ix_sensors_is_active', 'sensors', ['is_active'])

    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('source_system_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_customers_code'),
        sa.UniqueConstraint('source_system_id', name='uq_customers_source_system_id'),
    )
    op.create_index('ix_customers_code', 'customers', ['code'], unique=True)
    op.create_index('ix_customers_region', 'customers', ['region'])
    op.create_index('ix_customers_is_active', 'customers', ['is_active'])
    op.create_index('ix_customers_source_system_id', 'customers', ['source_system_id'], unique=True)

    # Create quality_specs table
    op.create_table(
        'quality_specs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.Column('parameter_name', sa.String(length=100), nullable=False),
        sa.Column('lower_limit', sa.DECIMAL(precision=15, scale=6), nullable=False),
        sa.Column('upper_limit', sa.DECIMAL(precision=15, scale=6), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'parameter_name', name='uq_quality_specs_product_param'),
    )
    op.create_index('ix_quality_specs_product_id', 'quality_specs', ['product_id'])
    op.create_index('ix_quality_specs_product_param', 'quality_specs', ['product_id', 'parameter_name'], unique=True)
    op.create_index('ix_quality_specs_is_active', 'quality_specs', ['is_active'])


def downgrade() -> None:
    # Drop indices (in reverse order)
    op.drop_index('ix_quality_specs_is_active', table_name='quality_specs')
    op.drop_index('ix_quality_specs_product_param', table_name='quality_specs')
    op.drop_index('ix_quality_specs_product_id', table_name='quality_specs')

    op.drop_index('ix_customers_source_system_id', table_name='customers')
    op.drop_index('ix_customers_is_active', table_name='customers')
    op.drop_index('ix_customers_region', table_name='customers')
    op.drop_index('ix_customers_code', table_name='customers')

    op.drop_index('ix_sensors_is_active', table_name='sensors')
    op.drop_index('ix_sensors_sensor_parameter_id', table_name='sensors')
    op.drop_index('ix_sensors_production_line_id', table_name='sensors')
    op.drop_index('ix_sensors_device_id', table_name='sensors')

    op.drop_index('ix_sensor_parameters_is_active', table_name='sensor_parameters')
    op.drop_index('ix_sensor_parameters_code', table_name='sensor_parameters')

    op.drop_index('ix_warehouses_source_system_id', table_name='warehouses')
    op.drop_index('ix_warehouses_is_active', table_name='warehouses')
    op.drop_index('ix_warehouses_code', table_name='warehouses')

    op.drop_index('ix_units_of_measure_source_system_id', table_name='units_of_measure')
    op.drop_index('ix_units_of_measure_code', table_name='units_of_measure')

    # Drop tables
    op.drop_table('quality_specs')
    op.drop_table('customers')
    op.drop_table('sensors')
    op.drop_table('sensor_parameters')
    op.drop_table('warehouses')
    op.drop_table('units_of_measure')
