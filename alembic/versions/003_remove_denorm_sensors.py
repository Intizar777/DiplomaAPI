"""Remove denormalized columns from sensor_readings table

Revision ID: 003_remove_denormalized_columns_from_sensor_readings
Revises: 002_add_fk_existing
Create Date: 2026-05-08 12:10:00.000000+00:00

After introducing sensor_id FK, remove denormalized fields:
- device_id (now in sensors table)
- production_line (now in sensors table via sensor_parameter)
- parameter_name (now in sensor_parameters table)
- unit (now in sensor_parameters table)

These columns are now accessed through the Sensor → SensorParameter relationship.
"""
from alembic import op
import sqlalchemy as sa


revision = '003_remove_denorm_sensors'
down_revision = '002_add_fk_existing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop indices first
    op.drop_index('ix_sensor_readings_device_id', table_name='sensor_readings', if_exists=True)
    op.drop_index('ix_sensor_readings_production_line', table_name='sensor_readings', if_exists=True)
    op.drop_index('ix_sensor_readings_parameter_name', table_name='sensor_readings', if_exists=True)

    # Recreate composite indices with sensor_id
    op.create_index(
        'ix_sensor_readings_sensor_recorded',
        'sensor_readings',
        ['sensor_id', 'recorded_at']
    )
    op.create_index(
        'ix_sensor_readings_recorded_quality',
        'sensor_readings',
        ['recorded_at', 'quality']
    )

    # Drop columns (make them nullable first if they aren't, then drop)
    op.drop_column('sensor_readings', 'device_id')
    op.drop_column('sensor_readings', 'production_line')
    op.drop_column('sensor_readings', 'parameter_name')
    op.drop_column('sensor_readings', 'unit')


def downgrade() -> None:
    # Restore columns (nullable, since we can't know original values)
    op.add_column('sensor_readings', sa.Column('unit', sa.String(length=20), nullable=True))
    op.add_column('sensor_readings', sa.Column('parameter_name', sa.String(length=50), nullable=True))
    op.add_column('sensor_readings', sa.Column('production_line', sa.String(length=50), nullable=True))
    op.add_column('sensor_readings', sa.Column('device_id', sa.String(length=100), nullable=True))

    # Restore indices
    op.create_index('ix_sensor_readings_parameter_name', 'sensor_readings', ['parameter_name'])
    op.create_index('ix_sensor_readings_production_line', 'sensor_readings', ['production_line'])
    op.create_index('ix_sensor_readings_device_id', 'sensor_readings', ['device_id'])

    # Drop new indices
    op.drop_index('ix_sensor_readings_recorded_quality', table_name='sensor_readings', if_exists=True)
    op.drop_index('ix_sensor_readings_sensor_recorded', table_name='sensor_readings', if_exists=True)
