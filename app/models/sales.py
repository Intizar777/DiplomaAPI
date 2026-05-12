"""
Sales aggregation models.
"""
from datetime import date

from sqlalchemy import Column, Date, DECIMAL, Integer, String, UniqueConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class AggregatedSales(Base, UUIDMixin, TimestampMixin):
    """
    Aggregated sales data by period and grouping type.
    """
    __tablename__ = "aggregated_sales"
    
    # Period
    period_from = Column(Date, nullable=False)
    period_to = Column(Date, nullable=False)
    
    # Grouping
    group_by_type = Column(String(20), nullable=False)  # 'region', 'channel', 'product'
    group_key = Column(String(100), nullable=False)       # actual value
    
    # Metrics
    total_quantity = Column(DECIMAL(15, 3), nullable=False, default=0)
    total_amount = Column(DECIMAL(15, 2), nullable=False, default=0)
    sales_count = Column(Integer, nullable=False, default=0)
    avg_order_value = Column(DECIMAL(15, 2), nullable=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('period_from', 'period_to', 'group_by_type', 'group_key',
                         name='uix_sales_period_group'),
        Index('idx_sales_period', 'period_from', 'period_to'),
        Index('idx_sales_group_type', 'group_by_type'),
    )
    
    def __repr__(self):
        return f"<AggregatedSales({self.group_by_type}={self.group_key}, {self.period_from}-{self.period_to})>"


class SalesTrends(Base, UUIDMixin, TimestampMixin):
    """
    Sales trends for time-series charts.
    """
    __tablename__ = "sales_trends"
    
    # Date and interval
    trend_date = Column(Date, nullable=False)
    interval_type = Column(String(10), nullable=False)  # 'day', 'week', 'month'
    
    # Filters (nullable = all)
    region = Column(String(100), nullable=True)
    channel = Column(String(50), nullable=True)
    
    # Metrics
    total_amount = Column(DECIMAL(15, 2), nullable=False, default=0)
    total_quantity = Column(DECIMAL(15, 3), nullable=False, default=0)
    order_count = Column(Integer, nullable=False, default=0)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('trend_date', 'interval_type', 'region', 'channel',
                         name='uix_trends_date_interval'),
        Index('idx_trends_date', 'trend_date'),
        Index('idx_trends_interval', 'interval_type'),
    )
    
    def __repr__(self):
        return f"<SalesTrends({self.trend_date}, {self.interval_type})>"


class SaleRecord(Base, UUIDMixin, TimestampMixin):
    """
    Raw sales records (synced from Gateway).
    Normalized: customer_id links to Customer table.
    """
    __tablename__ = "sale_records"

    external_id = Column(String(100), nullable=True, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_name = Column(String(255), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_name = Column(String(255), nullable=True)
    quantity = Column(DECIMAL(15, 3), nullable=True)
    amount = Column(DECIMAL(15, 2), nullable=True)
    cost = Column(DECIMAL(15, 2), nullable=True)
    sale_date = Column(Date, nullable=False, index=True)
    region = Column(String(100), nullable=True, index=True)
    channel = Column(String(50), nullable=True, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    event_id = Column(UUID(as_uuid=True), nullable=True, unique=True, index=True)

    __table_args__ = (
        Index('idx_sale_records_product_date', 'product_id', 'sale_date'),
        Index('idx_sale_records_customer_date', 'customer_id', 'sale_date'),
        Index('idx_sale_records_channel_date', 'channel', 'sale_date'),
    )

    def __repr__(self):
        return f"<SaleRecord(external_id={self.external_id}, date={self.sale_date})>"
