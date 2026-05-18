"""add sensor_anomalies table

Revision ID: f003
Revises: f002
Create Date: 2026-05-17 21:50:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'f003'
down_revision = 'f002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sensor_anomalies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('reading_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('device_id', sa.String(50), nullable=False, index=True),
        sa.Column('production_line_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('parameter_name', sa.String(100), nullable=False),
        sa.Column('value', sa.DECIMAL(12, 4), nullable=True),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('quality', sa.String(20), nullable=True),
        sa.Column('anomaly_type', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False, index=True),
        sa.Column('reason', sa.String(500), nullable=True),
        sa.Column('lower_limit', sa.DECIMAL(12, 4), nullable=True),
        sa.Column('upper_limit', sa.DECIMAL(12, 4), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('event_id', sa.String(255), nullable=True, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        'ix_sensor_anomalies_detected_at_severity',
        'sensor_anomalies',
        ['detected_at', 'severity'],
    )


def downgrade() -> None:
    op.drop_table('sensor_anomalies')
