"""
Output (production batch) models.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import Column, Date, String, DECIMAL, Index
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class ProductionOutput(Base, UUIDMixin, TimestampMixin):
    """
    Production output records (batch/lot level).
    Denormalized: production_line_name for reporting without JOIN.
    """
    __tablename__ = "production_output"

    order_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_name = Column(String(255), nullable=True)
    production_line_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    production_line_name = Column(String(255), nullable=True)
    lot_number = Column(String(100), nullable=False, index=True)
    quantity = Column(DECIMAL(15, 3), nullable=True)
    quality_status = Column(String(20), nullable=True)
    production_date = Column(Date, nullable=False, index=True)
    shift = Column(String(20), nullable=True, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    event_id = Column(UUID(as_uuid=True), nullable=True, unique=True, index=True)

    __table_args__ = (
        Index('idx_output_date_shift', 'production_date', 'shift'),
        Index('idx_output_product_date', 'product_id', 'production_date'),
    )

    def __repr__(self):
        return f"<ProductionOutput(lot={self.lot_number}, date={self.production_date})>"
