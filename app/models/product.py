"""
Product reference models.
"""
from sqlalchemy import Column, String, Boolean, Integer, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class Product(Base, UUIDMixin, TimestampMixin):
    """
    Product reference data (synced from Gateway).
    Normalized: unit_of_measure_id links to UnitOfMeasure table.
    """
    __tablename__ = "products"

    code = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=True, index=True)
    brand = Column(String(255), nullable=True, index=True)
    unit_of_measure_id = Column(UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="SET NULL"), nullable=True, index=True)
    shelf_life_days = Column(Integer, nullable=True)
    requires_quality_check = Column(Boolean, nullable=True, default=False)
    source_system_id = Column(String(100), nullable=True)
    event_id = Column(UUID(as_uuid=True), nullable=True, unique=True, index=True)

    __table_args__ = (
        Index('idx_products_category_brand', 'category', 'brand'),
        Index('idx_products_unit_of_measure', 'unit_of_measure_id'),
    )

    def __repr__(self):
        return f"<Product(code={self.code}, name={self.name})>"
