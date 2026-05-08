"""
Sensor reading models.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, String, DECIMAL, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class SensorReading(Base, UUIDMixin, TimestampMixin):
    """
    IoT sensor readings history.
    Normalized: sensor_id links to Sensor table which contains device_id, parameter info, etc.
    """
    __tablename__ = "sensor_readings"

    sensor_id = Column(UUID(as_uuid=True), ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(DECIMAL(12, 4), nullable=True)
    quality = Column(String(20), nullable=True, index=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    snapshot_date = Column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index('idx_sensor_reading_sensor_recorded', 'sensor_id', 'recorded_at'),
        Index('idx_sensor_reading_recorded_quality', 'recorded_at', 'quality'),
    )

    def __repr__(self):
        return f"<SensorReading(sensor_id={self.sensor_id}, recorded_at={self.recorded_at})>"
