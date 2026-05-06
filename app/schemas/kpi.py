"""
KPI API schemas.
"""
from datetime import date
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


class KPIData(BaseModel):
    """Individual KPI data point."""
    total_output: Decimal = Field(description="Total production output")
    defect_rate: Decimal = Field(description="Defect rate percentage")
    completed_orders: int = Field(description="Number of completed orders")
    total_orders: int = Field(description="Total number of orders")
    oee_estimate: Optional[Decimal] = Field(default=None, description="OEE estimate percentage")
    production_line: Optional[str] = Field(default=None, description="Production line")


class KPICurrentResponse(BaseModel):
    """Current KPI response."""
    data: KPIData
    period_from: date = Field(description="Period start date")
    period_to: date = Field(description="Period end date")
    
    class Config:
        from_attributes = True


class KPIHistoryItem(BaseModel):
    """Single KPI history record."""
    period_from: date
    period_to: date
    production_line: Optional[str]
    total_output: Decimal
    defect_rate: Decimal
    completed_orders: int
    total_orders: int
    oee_estimate: Optional[Decimal]


class KPIHistoryResponse(BaseModel):
    """KPI history response."""
    items: List[KPIHistoryItem]
    period_from: date
    period_to: date
    
    class Config:
        from_attributes = True


class KPIComparisonData(BaseModel):
    """KPI data for comparison period."""
    period_from: date
    period_to: date
    total_output: Decimal
    defect_rate: Decimal
    completed_orders: int
    total_orders: int
    oee_estimate: Optional[Decimal]


class KPICompareResponse(BaseModel):
    """KPI comparison response."""
    period1: KPIComparisonData
    period2: KPIComparisonData
    
    # Comparison metrics
    output_change_percent: Decimal = Field(description="Total output change %")
    defect_rate_change: Decimal = Field(description="Defect rate change (percentage points)")
    order_completion_change: Decimal = Field(description="Order completion rate change %")
    
    class Config:
        from_attributes = True
