"""
Analytics models: BatchInput, DowntimeEvent, PromoCampaign.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, DECIMAL, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class BatchInput(Base, UUIDMixin, TimestampMixin):
    """Raw material batch intake record."""
    __tablename__ = "batch_inputs"

    order_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    quantity = Column(DECIMAL(15, 3), nullable=False)
    input_date = Column(DateTime(timezone=True), nullable=False, index=True)
    event_id = Column(String(255), nullable=True, unique=True)

    __table_args__ = (
        Index("ix_batch_inputs_input_date", "input_date"),
    )

    def __repr__(self):
        return f"<BatchInput(order_id={self.order_id}, qty={self.quantity})>"


class DowntimeEvent(Base, UUIDMixin, TimestampMixin):
    """Equipment downtime event."""
    __tablename__ = "downtime_events"

    production_line_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    reason = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    event_id = Column(String(255), nullable=True, unique=True)

    def __repr__(self):
        return f"<DowntimeEvent(category={self.category}, duration={self.duration_minutes}m)>"


class PromoCampaign(Base, UUIDMixin, TimestampMixin):
    """Promotional campaign."""
    __tablename__ = "promo_campaigns"

    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    channel = Column(String(50), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    discount_percent = Column(DECIMAL(5, 2), nullable=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True)
    budget = Column(DECIMAL(15, 2), nullable=True)
    event_id = Column(String(255), nullable=True, unique=True)

    def __repr__(self):
        return f"<PromoCampaign(name={self.name}, channel={self.channel})>"
