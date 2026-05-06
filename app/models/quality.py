"""
Quality control models.
"""
from datetime import date

from sqlalchemy import Column, Date, String, DECIMAL, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin, QualityDecision


class QualityResult(Base, UUIDMixin, TimestampMixin):
    """
    Quality control test results.
    """
    __tablename__ = "quality_results"
    
    # Lot and product
    lot_number = Column(String(100), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_name = Column(String(255), nullable=True)
    
    # Test parameters
    parameter_name = Column(String(50), nullable=False)
    result_value = Column(DECIMAL(10, 4), nullable=True)
    lower_limit = Column(DECIMAL(10, 4), nullable=True)
    upper_limit = Column(DECIMAL(10, 4), nullable=True)
    
    # Decision
    in_spec = Column(Boolean, nullable=False, default=True)
    decision = Column(String(20), nullable=False, index=True)  # QualityDecision value
    
    # Test date
    test_date = Column(Date, nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_quality_date_decision', 'test_date', 'decision'),
        Index('idx_quality_product_date', 'product_id', 'test_date'),
    )
    
    def __repr__(self):
        return f"<QualityResult(lot={self.lot_number}, param={self.parameter_name}, decision={self.decision})>"
