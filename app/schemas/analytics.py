"""
Analytics API schemas for production KPI, sales, batch-inputs, downtime, promo campaigns.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Literal

from pydantic import BaseModel, Field


# ============ Batch Inputs ============

class BatchInputCreate(BaseModel):
    """Create batch input request."""
    order_id: Optional[str] = Field(None, description="Order UUID")
    product_id: Optional[str] = Field(None, description="Product UUID")
    quantity: Decimal = Field(..., description="Quantity (with 3 decimals)")
    input_date: datetime = Field(..., description="Input datetime")


class BatchInputResponse(BaseModel):
    """Batch input response."""
    id: str = Field(..., description="Batch input UUID")
    order_id: Optional[str]
    product_id: Optional[str]
    quantity: Decimal
    input_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BatchInputListResponse(BaseModel):
    """Batch input list response."""
    items: List[BatchInputResponse]
    total: int


class YieldResponse(BaseModel):
    """Yield ratio response (input to output)."""
    order_id: str = Field(..., description="Order UUID")
    total_input: Decimal = Field(..., description="Total input quantity")
    total_output: Decimal = Field(..., description="Total output quantity")
    yield_percent: Decimal = Field(..., description="Yield as percentage (output/input * 100)")
    target: Decimal = Field(..., description="Target yield percentage")


# ============ Downtime Events ============

class DowntimeEventCreate(BaseModel):
    """Create downtime event request."""
    production_line_id: Optional[str] = Field(None, description="Production line UUID")
    reason: str = Field(..., description="Reason for downtime")
    category: Literal[
        "PLANNED_MAINTENANCE",
        "UNPLANNED_BREAKDOWN",
        "QUALITY_ISSUE",
        "MATERIAL_SHORTAGE",
        "OTHER"
    ] = Field(..., description="Downtime category")
    started_at: datetime = Field(..., description="Downtime start datetime")
    ended_at: Optional[datetime] = Field(None, description="Downtime end datetime")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")


class DowntimeEventResponse(BaseModel):
    """Downtime event response."""
    id: str = Field(..., description="Event UUID")
    production_line_id: Optional[str]
    reason: str
    category: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DowntimeEventListResponse(BaseModel):
    """Downtime event list response."""
    items: List[DowntimeEventResponse]
    total: int


class DowntimeSummaryItem(BaseModel):
    """Single downtime summary entry."""
    category: str = Field(..., description="Downtime category")
    total_minutes: int = Field(..., description="Total downtime minutes for category")
    count: int = Field(..., description="Number of downtime events in category")


class DowntimeSummaryResponse(BaseModel):
    """Downtime summary (aggregated by category)."""
    items: List[DowntimeSummaryItem]
    total_events: int = Field(..., description="Total number of downtime events")
    total_downtime_minutes: int = Field(..., description="Total downtime minutes across all categories")


# ============ Promo Campaigns ============

class PromoCampaignCreate(BaseModel):
    """Create promo campaign request."""
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    channel: Literal["DIRECT", "DISTRIBUTOR", "RETAIL", "ONLINE"] = Field(..., description="Sales channel")
    product_id: Optional[str] = Field(None, description="Product UUID")
    discount_percent: Optional[Decimal] = Field(None, description="Discount percentage")
    start_date: date = Field(..., description="Campaign start date")
    end_date: Optional[date] = Field(None, description="Campaign end date")
    budget: Optional[Decimal] = Field(None, description="Campaign budget")


class PromoCampaignResponse(BaseModel):
    """Promo campaign response."""
    id: str = Field(..., description="Campaign UUID")
    name: str
    description: Optional[str]
    channel: str
    product_id: Optional[str]
    discount_percent: Optional[Decimal]
    start_date: date
    end_date: Optional[date]
    budget: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromoCampaignListResponse(BaseModel):
    """Promo campaign list response."""
    items: List[PromoCampaignResponse]
    total: int


class PromoCampaignEffectivenessResponse(BaseModel):
    """Campaign effectiveness (ROI, uplift)."""
    campaign_id: str = Field(..., description="Campaign UUID")
    campaign_name: str = Field(..., description="Campaign name")
    budget: Optional[Decimal] = Field(..., description="Campaign budget")
    sales_during_campaign: Decimal = Field(..., description="Total sales during campaign period")
    baseline_sales: Decimal = Field(..., description="Baseline sales (without campaign)")
    uplift: Decimal = Field(..., description="Sales uplift (actual - baseline)")
    cost_per_uplift_unit: Optional[Decimal] = Field(None, description="Cost per unit of uplift")
    roi: Decimal = Field(..., description="ROI (uplift / budget)")
    roi_percent: Decimal = Field(..., description="ROI as percentage")


# ============ Enhanced KPI Response (targets, trends, comparison) ============

class KPITarget(BaseModel):
    """Single KPI target with status."""
    target: Decimal = Field(..., description="Target value")
    min: Decimal = Field(..., description="Minimum acceptable value")
    max: Decimal = Field(..., description="Maximum acceptable value")
    status: Literal["ok", "warning", "critical"] = Field(..., description="Status based on current value")


class KPITargets(BaseModel):
    """All KPI targets."""
    oee_estimate: Optional[KPITarget] = None
    defect_rate: Optional[KPITarget] = None
    otif_rate: Optional[KPITarget] = None


class KPITrendPoint(BaseModel):
    """Single KPI trend data point."""
    period: str = Field(..., description="Date or period label (YYYY-MM-DD)")
    total_output: Decimal
    defect_rate: Decimal
    oee_estimate: Optional[Decimal] = None


class KPIResponse(BaseModel):
    """Enhanced KPI response with targets, trends, comparison."""
    total_output: Decimal
    defect_rate: Decimal
    completed_orders: int
    total_orders: int
    availability: Decimal = Field(..., description="Availability percentage (0-1)")
    performance: Decimal = Field(..., description="Performance percentage (0-1)")
    oee_estimate: Decimal = Field(..., description="OEE estimate (0-1)")
    line_throughput: Decimal = Field(..., description="Line throughput")
    targets: KPITargets = Field(..., description="Target values with status")
    trend: List[KPITrendPoint] = Field(..., description="Trend data points")
    change_percent: Optional[dict] = Field(None, description="Change % from previous period (totalOutput, oeeEstimate, etc.)")


# ============ OTIF (On-Time In-Full) ============

class OTIFResponse(BaseModel):
    """OTIF metrics response."""
    otif_rate: Decimal = Field(..., description="OTIF rate (0-1)")
    on_time_orders: int = Field(..., description="Orders completed on time")
    in_full_quantity_orders: int = Field(..., description="Orders completed in full quantity")
    otif_orders: int = Field(..., description="Orders both on-time and in-full")
    total_orders: int = Field(..., description="Total orders in period")


# ============ KPI Breakdown (drill-down) ============

class KPIBreakdownItem(BaseModel):
    """Single KPI breakdown row (by line, product, division)."""
    group_key: str = Field(..., description="Line ID, product ID, or division name")
    value: Decimal = Field(..., description="Metric value")
    target: Optional[Decimal] = Field(None, description="Target value")
    status: Literal["ok", "warning", "critical"] = Field(..., description="Status vs target")
    deviation: Optional[Decimal] = Field(None, description="Deviation from target (value - target)")


class KPIBreakdownResponse(BaseModel):
    """KPI breakdown response (aggregated by group)."""
    items: List[KPIBreakdownItem]
    total: int = Field(..., description="Total number of groups")


# ============ Sales Margin ============

class SalesMarginItem(BaseModel):
    """Single product margin."""
    product_id: str = Field(..., description="Product UUID")
    product_code: str = Field(..., description="Product code")
    product_name: str = Field(..., description="Product name")
    total_quantity: Decimal
    total_revenue: Decimal
    total_cost: Decimal
    total_margin: Decimal
    margin_percent: Decimal = Field(..., description="Margin as percentage")
    margin_per_unit: Decimal


class SalesMarginAggregated(BaseModel):
    """Aggregated margin metrics."""
    total_revenue: Decimal
    total_cost: Decimal
    total_margin: Decimal
    avg_margin_percent: Decimal


class SalesMarginResponse(BaseModel):
    """Sales margin response."""
    margins: List[SalesMarginItem]
    total: int = Field(..., description="Total number of products")
    aggregated: SalesMarginAggregated


# ============ Production Lines ============

class ProductionLineResponse(BaseModel):
    """Production line reference."""
    id: str = Field(..., description="Line UUID")
    code: str = Field(..., description="Line code")
    name: str = Field(..., description="Line name")
    description: Optional[str]
    division: Optional[str] = Field(None, description="Division/department name")
    is_active: bool


class ProductionLinesListResponse(BaseModel):
    """Production lines list."""
    production_lines: List[ProductionLineResponse]
    total: int


# ============ Line Productivity (Phase 2) ============

class LineProductivityItem(BaseModel):
    """Line productivity data point."""
    production_line: str = Field(..., description="Production line code/name")
    productivity: Decimal = Field(..., description="Productivity in tonnes/hour")
    total_output: Decimal = Field(..., description="Total output in tonnes")
    days: int = Field(..., description="Number of days in period")
    target: Decimal = Field(..., description="Target productivity")
    status: Literal["ok", "warning", "critical"] = Field(..., description="Status vs target")
    deviation: Decimal = Field(..., description="Deviation from target")


class LineProductivityResponse(BaseModel):
    """Line productivity response."""
    items: List[LineProductivityItem]
    period: dict = Field(..., description="Period from/to dates")
    unit: str = Field(..., description="Unit of measurement")


# ============ Scrap Percentage (Phase 2) ============

class ScrapPercentageResponse(BaseModel):
    """Scrap percentage (quality defects) response."""
    scrap_percentage: Decimal = Field(..., description="Scrap percentage")
    rejected_tests: int = Field(..., description="Number of rejected quality tests")
    total_tests: int = Field(..., description="Total number of quality tests")
    target: Decimal = Field(..., description="Target scrap percentage")
    status: Literal["ok", "warning", "critical"] = Field(..., description="Status vs target")
    period: dict = Field(..., description="Period from/to dates")


# ============ Marginality (Phase 3) ============

class MarginalityResponse(BaseModel):
    """Marginality (profit margin) response."""
    margin_percent: Decimal = Field(..., description="Margin as percentage")
    total_revenue: Decimal = Field(..., description="Total revenue")
    material_cost: Decimal = Field(..., description="Total material cost")
    margin: Decimal = Field(..., description="Margin value (revenue - cost)")
    target: Decimal = Field(..., description="Target margin percentage")
    status: Literal["ok", "warning", "critical"] = Field(..., description="Status vs target")
    period: dict = Field(..., description="Period from/to dates")


# ============ Cost Per KG (Phase 3) ============

class CostPerKgResponse(BaseModel):
    """Cost per kg (COGS per unit) response."""
    cost_per_kg: Decimal = Field(..., description="Cost per kilogram")
    total_cost: Decimal = Field(..., description="Total cost")
    total_output: Decimal = Field(..., description="Total output in kg")
    period: dict = Field(..., description="Period from/to dates")


# ============ EBITDA (Phase 3) ============

class EBITDAResponse(BaseModel):
    """EBITDA response."""
    ebitda_million_rub: Decimal = Field(..., description="EBITDA in million rubles")
    ebitda_value: Decimal = Field(..., description="EBITDA value in rubles")
    total_revenue: Decimal = Field(..., description="Total revenue")
    operating_costs: Decimal = Field(..., description="Operating costs")
    ebitda_margin_percent: Decimal = Field(..., description="EBITDA margin as percentage")
    target_million_rub: Optional[Decimal] = Field(None, description="Target EBITDA in million rubles")
    period: dict = Field(..., description="Period from/to dates")


# ============ Market Share (Phase 3) ============

class MarketShareResponse(BaseModel):
    """Market share response."""
    market_share_percent: Decimal = Field(..., description="Market share as percentage")
    company_volume_tonnes: Decimal = Field(..., description="Company sales volume in tonnes")
    market_total_tonnes: Optional[Decimal] = Field(None, description="Total market volume in tonnes")
    period: dict = Field(..., description="Period from/to dates")


# ============ Cost Base Management ============

class CostBaseCreate(BaseModel):
    """Create cost base request."""
    product_id: Optional[str] = Field(None, description="Product UUID (NULL = global default)")
    raw_material_cost: Decimal = Field(..., description="Raw material cost per kg")
    labor_cost_per_hour: Optional[Decimal] = Field(None, description="Labor cost per hour")
    depreciation_monthly: Optional[Decimal] = Field(None, description="Monthly depreciation")
    period_from: date = Field(..., description="Period start date")
    period_to: Optional[date] = Field(None, description="Period end date (NULL = still active)")


class CostBaseResponse(BaseModel):
    """Cost base response."""
    id: str = Field(..., description="Cost base UUID")
    product_id: Optional[str]
    raw_material_cost: Decimal
    labor_cost_per_hour: Optional[Decimal]
    depreciation_monthly: Optional[Decimal]
    period_from: date
    period_to: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CostBaseListResponse(BaseModel):
    """Cost base list response."""
    items: List[CostBaseResponse]
    total: int
    offset: int
    limit: int


# ============ KPI Configuration ============

class KPIConfigCreate(BaseModel):
    """Create KPI config request."""
    key: str = Field(..., description="Config key (e.g. 'market_total_volume_tonnes')")
    value: Decimal = Field(..., description="Config value")
    description: Optional[str] = Field(None, description="Config description")
    updated_by: Optional[str] = Field(None, description="Updated by user")


class KPIConfigResponse(BaseModel):
    """KPI config response."""
    id: str = Field(..., description="Config UUID")
    key: str
    value: Decimal
    description: Optional[str]
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
