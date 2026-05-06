"""
Sensor reading models.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, String, DECIMAL, Index
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class SensorReading(Base, UUIDMixin, TimestampMixin):
    """
    IoT sensor readings history.
    """
    __tablename__ = "sensor_readings"

    device_id = Column(String(100), nullable=False, index=True)
    production_line = Column(String(50), nullable=False, index=True)
    parameter_name = Column(String(50), nullable=False, index=True)
    value = Column(DECIMAL(12, 4), nullable=True)
    unit = Column(String(20), nullable=True)
    quality = Column(String(20), nullable=True, index=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    snapshot_date = Column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index('idx_sensor_line_param', 'production_line', 'parameter_name'),
        Index('idx_sensor_line_date', 'production_line', 'recorded_at'),
    )

    def __repr__(self):
        return f"<SensorReading(device={self.device_id}, param={self.parameter_name})>"
