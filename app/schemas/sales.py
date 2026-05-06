"""
Sales API schemas.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class SalesSummaryItem(BaseModel):
    """Single sales summary record."""
    group_key: str = Field(description="Group identifier (region, channel, product)")
    total_quantity: Decimal = Field(description="Total quantity sold")
    total_amount: Decimal = Field(description="Total amount (revenue)")
    sales_count: int = Field(description="Number of sales transactions")
    avg_order_value: Optional[Decimal] = Field(default=None, description="Average order value")


class SalesSummaryResponse(BaseModel):
    """Sales summary response."""
    summary: List[SalesSummaryItem]
    total_amount: Decimal = Field(description="Grand total amount")
    total_quantity: Decimal = Field(description="Grand total quantity")
    period_from: date
    period_to: date
    group_by: Literal["region", "channel", "product"] = Field(description="Grouping type")
    
    class Config:
        from_attributes = True


class SalesTrendPoint(BaseModel):
    """Single sales trend data point."""
    trend_date: date
    total_amount: Decimal
    total_quantity: Decimal
    order_count: int


class SalesTrendsResponse(BaseModel):
    """Sales trends response."""
    trends: List[SalesTrendPoint]
    interval: Literal["day", "week", "month"] = Field(description="Trend interval")
    period_from: date
    period_to: date
    region: Optional[str] = None
    channel: Optional[str] = None
    
    class Config:
        from_attributes = True


class TopProductItem(BaseModel):
    """Top product item."""
    product_id: str
    product_name: str
    total_quantity: Decimal
    total_amount: Decimal
    sales_count: int


class TopProductsResponse(BaseModel):
    """Top products response."""
    products: List[TopProductItem]
    period_from: date
    period_to: date
    limit: int
    
    class Config:
        from_attributes = True


class SalesRegionItem(BaseModel):
    """Sales by region item."""
    region: str
    total_quantity: Decimal
    total_amount: Decimal
    sales_count: int
    percentage: Decimal = Field(description="Percentage of total sales")


class SalesRegionsResponse(BaseModel):
    """Sales by regions response."""
    regions: List[SalesRegionItem]
    period_from: date
    period_to: date
    
    class Config:
        from_attributes = True
