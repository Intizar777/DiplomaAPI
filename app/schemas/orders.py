"""
Orders API schemas.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class OrderStatusCount(BaseModel):
    """Order count by status."""
    planned: int = 0
    in_progress: int = 0
    completed: int = 0
    cancelled: int = 0


class OrderStatusSummaryResponse(BaseModel):
    """Order status summary response."""
    by_status: OrderStatusCount
    by_production_line: Dict[str, OrderStatusCount] = Field(
        description="Status breakdown by production line"
    )
    period_from: date
    period_to: date
    
    class Config:
        from_attributes = True


class OrderListItem(BaseModel):
    """Order list item."""
    order_id: str
    external_order_id: Optional[str]
    product_id: str
    product_name: Optional[str]
    target_quantity: Optional[Decimal]
    actual_quantity: Optional[Decimal]
    unit_of_measure: Optional[str]
    status: str
    production_line: Optional[str]
    planned_start: Optional[datetime]
    planned_end: Optional[datetime]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    snapshot_date: date
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Order list response."""
    orders: List[OrderListItem]
    total: int
    page: int
    limit: int
    pages: int
    
    class Config:
        from_attributes = True


class OrderOutputItem(BaseModel):
    """Order output item."""
    output_id: str
    lot_number: str
    quantity: Decimal
    quality_status: str
    production_date: date
    shift: str


class OrderDetailResponse(BaseModel):
    """Order detail response."""
    order_id: str
    external_order_id: Optional[str]
    product_id: str
    product_name: Optional[str]
    target_quantity: Optional[Decimal]
    actual_quantity: Optional[Decimal]
    unit_of_measure: Optional[str]
    status: str
    production_line: Optional[str]
    planned_start: Optional[datetime]
    planned_end: Optional[datetime]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    outputs: List[OrderOutputItem] = []

    class Config:
        from_attributes = True


class PlanExecutionLineItem(BaseModel):
    production_line: Optional[str]
    target_quantity: Decimal
    actual_quantity: Decimal
    fulfillment_pct: Decimal
    total_orders: int
    completed_orders: int
    in_progress_orders: int
    overdue_orders: int

    class Config:
        from_attributes = True


class PlanExecutionResponse(BaseModel):
    period_from: date
    period_to: date
    lines: List[PlanExecutionLineItem]

    class Config:
        from_attributes = True


class DowntimeLineItem(BaseModel):
    rank: int
    production_line: Optional[str]
    total_delay_hours: Decimal
    order_count: int
    avg_delay_per_order: Decimal
    cumulative_pct: Decimal

    class Config:
        from_attributes = True


class DowntimeResponse(BaseModel):
    total_delay_hours: Decimal
    period_from: date
    period_to: date
    lines: List[DowntimeLineItem]

    class Config:
        from_attributes = True
