"""
Sensor anomaly model.
"""
from decimal import Decimal
from typing import Any

from sqlalchemy import Column, DateTime, String, DECIMAL, Index
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class SensorAnomaly(Base, UUIDMixin, TimestampMixin):
    """Sensor anomaly detected from readings."""
    __tablename__ = "sensor_anomalies"

    reading_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    production_line_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    parameter_name = Column(String(100), nullable=False)
    value: Column[Any] = Column(DECIMAL(12, 4), nullable=True)
    unit = Column(String(20), nullable=True)
    quality = Column(String(20), nullable=True)
    anomaly_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    reason = Column(String(500), nullable=True)
    lower_limit: Column[Any] = Column(DECIMAL(12, 4), nullable=True)
    upper_limit: Column[Any] = Column(DECIMAL(12, 4), nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    event_id = Column(String(255), nullable=True, unique=True)

    __table_args__ = (
        Index("ix_sensor_anomalies_detected_at_severity", "detected_at", "severity"),
    )

    def __repr__(self) -> str:
        return f"<SensorAnomaly(device={self.device_id}, type={self.anomaly_type}, severity={self.severity})>"
