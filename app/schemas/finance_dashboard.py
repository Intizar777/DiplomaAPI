"""
Finance Manager Dashboard schemas.
"""
from datetime import date as date_type
from decimal import Decimal
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class GroupByType(str, Enum):
    channel = "channel"
    region = "region"
    product = "product"


class IntervalType(str, Enum):
    day = "day"
    week = "week"
    month = "month"


class SortBy(str, Enum):
    amount = "amount"
    quantity = "quantity"


# ---------------------------------------------------------------------------
# Endpoint 1 — Sales Breakdown
# ---------------------------------------------------------------------------

class SalesGroupItem(BaseModel):
    """Aggregated sales for a single group (channel, region, or product name)."""

    group_key: str = Field(description="The group value (e.g. 'wholesale', 'North', 'Product Alpha').")
    total_amount: Decimal = Field(description="Sum of amount for this group in the period (2dp).")
    total_quantity: Decimal = Field(description="Sum of quantity for this group in the period (3dp).")
    sales_count: int = Field(description="Number of sale records for this group.")
    avg_order_value: Decimal = Field(description="total_amount / sales_count (2dp; 0 if no sales).")
    amount_share_pct: Decimal = Field(description="This group's share of total_amount * 100 (2dp).")

    model_config = ConfigDict(from_attributes=True)


class SalesBreakdownResponse(BaseModel):
    """Sales breakdown by channel/region/product for the Finance Manager Dashboard."""

    period_from: date_type = Field(description="Start of the analysis period.")
    period_to: date_type = Field(description="End of the analysis period.")
    group_by: GroupByType = Field(description="Dimension used for grouping.")
    total_amount: Decimal = Field(description="Grand total amount across all groups (2dp).")
    total_quantity: Decimal = Field(description="Grand total quantity across all groups (3dp).")
    groups: List[SalesGroupItem] = Field(description="Groups ranked descending by total_amount.")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Endpoint 2 — Revenue Trend
# ---------------------------------------------------------------------------

class RevenueTrendPoint(BaseModel):
    """Single interval data point for the revenue trend chart."""

    trend_date: date_type = Field(description="Start date of the interval bucket.")
    total_amount: Decimal = Field(description="Total revenue for this interval (2dp).")
    total_quantity: Decimal = Field(description="Total quantity for this interval (3dp).")
    order_count: int = Field(description="Number of sale records in this interval.")
    mom_growth_pct: Optional[Decimal] = Field(
        default=None,
        description="Period-over-period growth % vs previous interval (2dp; None for first point).",
    )

    model_config = ConfigDict(from_attributes=True)


class RevenueTrendResponse(BaseModel):
    """Revenue trend over time for the Finance Manager Dashboard."""

    period_from: date_type = Field(description="Start of the analysis period.")
    period_to: date_type = Field(description="End of the analysis period.")
    interval: IntervalType = Field(description="Aggregation interval (day/week/month).")
    region: Optional[str] = Field(default=None, description="Region filter applied (None = all).")
    channel: Optional[str] = Field(default=None, description="Channel filter applied (None = all).")
    data: List[RevenueTrendPoint] = Field(description="Data points ordered ascending by trend_date.")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Endpoint 3 — Top Products
# ---------------------------------------------------------------------------

class TopProductItem(BaseModel):
    """Revenue/volume summary for a single product."""

    rank: int = Field(description="Position in the ranking (1 = top).")
    product_name: str = Field(description="Product name.")
    total_amount: Decimal = Field(description="Total revenue for this product (2dp).")
    total_quantity: Decimal = Field(description="Total quantity sold (3dp).")
    sales_count: int = Field(description="Number of sale records for this product.")
    amount_share_pct: Decimal = Field(description="This product's share of total_amount * 100 (2dp).")

    model_config = ConfigDict(from_attributes=True)


class TopProductsResponse(BaseModel):
    """Top products ranked by amount or quantity for the Finance Manager Dashboard."""

    period_from: date_type = Field(description="Start of the analysis period.")
    period_to: date_type = Field(description="End of the analysis period.")
    sort_by: SortBy = Field(description="Sort dimension: 'amount' or 'quantity'.")
    total_amount: Decimal = Field(description="Grand total amount across all products (2dp).")
    products: List[TopProductItem] = Field(description="Products ranked descending by sort_by field.")

    model_config = ConfigDict(from_attributes=True)
