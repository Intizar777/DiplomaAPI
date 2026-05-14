"""
KPI aggregation models.
"""
from datetime import date

from sqlalchemy import Column, Date, DECIMAL, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class AggregatedKPI(Base, UUIDMixin, TimestampMixin):
    """
    Aggregated KPI metrics by period and production line.
    Denormalized: production_line_name for reporting without JOIN.
    """
    __tablename__ = "aggregated_kpi"

    # Period
    period_from = Column(Date, nullable=False, index=True)
    period_to = Column(Date, nullable=False, index=True)

    # Production line (NULL = all lines)
    production_line = Column(String(50), nullable=True, index=True)
    production_line_name = Column(String(255), nullable=True)
    
    # Metrics
    total_output = Column(DECIMAL(15, 3), nullable=False, default=0)
    defect_rate = Column(DECIMAL(5, 2), nullable=False, default=0)
    completed_orders = Column(Integer, nullable=False, default=0)
    total_orders = Column(Integer, nullable=False, default=0)
    oee_estimate = Column(DECIMAL(5, 2), nullable=True)
    avg_order_completion_time = Column(String(50), nullable=True)  # Stored as interval string
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('period_from', 'period_to', 'production_line', 
                         name='uix_kpi_period_line'),
    )
    
    def __repr__(self):
        return f"<AggregatedKPI({self.period_from} to {self.period_to}, line={self.production_line})>"
