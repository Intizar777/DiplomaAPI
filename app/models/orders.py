"""
Order snapshot models.
"""
from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, String, Index, DECIMAL
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin, OrderStatus


class OrderSnapshot(Base, UUIDMixin, TimestampMixin):
    """
    Historical snapshots of production orders.
    """
    __tablename__ = "order_snapshots"
    
    # Order identifiers
    order_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    external_order_id = Column(String(100), nullable=True)
    
    # Product info
    product_id = Column(UUID(as_uuid=True), nullable=False)
    product_name = Column(String(255), nullable=True)
    
    # Quantities
    target_quantity = Column(DECIMAL(15, 3), nullable=True)
    actual_quantity = Column(DECIMAL(15, 3), nullable=True)
    unit_of_measure = Column(String(20), nullable=True)
    
    # Status and line
    status = Column(String(20), nullable=False, index=True)  # OrderStatus value
    production_line = Column(String(50), nullable=True, index=True)
    
    # Dates
    planned_start = Column(DateTime(timezone=True), nullable=True)
    planned_end = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    
    # Snapshot date (when this record was captured)
    snapshot_date = Column(Date, nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_order_snapshots_composite', 'snapshot_date', 'status', 'production_line'),
    )
    
    def __repr__(self):
        return f"<OrderSnapshot(order={self.order_id}, date={self.snapshot_date}, status={self.status})>"
