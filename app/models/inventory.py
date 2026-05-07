"""
Inventory snapshot models.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, String, DECIMAL, Index
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class InventorySnapshot(Base, UUIDMixin, TimestampMixin):
    """
    Warehouse inventory snapshots.
    """
    __tablename__ = "inventory_snapshots"

    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_name = Column(String(255), nullable=True)
    warehouse_code = Column(String(50), nullable=False, index=True)
    lot_number = Column(String(100), nullable=True)
    quantity = Column(DECIMAL(15, 3), nullable=True)
    unit_of_measure = Column(String(20), nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    event_id = Column(UUID(as_uuid=True), nullable=True, unique=True, index=True)

    __table_args__ = (
        Index('idx_inventory_product_warehouse', 'product_id', 'warehouse_code'),
        Index('idx_inventory_date_warehouse', 'snapshot_date', 'warehouse_code'),
    )

    def __repr__(self):
        return f"<InventorySnapshot(product={self.product_id}, warehouse={self.warehouse_code})>"
