"""
Production Analytics API routes — enriched KPI, sales, batch-inputs, downtime, promo campaigns.
"""
from datetime import date, datetime
from typing import Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import (
    GatewayClient,
    BatchInputService,
    DowntimeEventService,
    PromoCampaignService,
    ProductionAnalyticsService,
    PersonnelService,
    CostBaseService,
)
from app.schemas import (
    BatchInputCreate,
    BatchInputResponse,
    BatchInputListResponse,
    YieldResponse,
    DowntimeEventCreate,
    DowntimeEventResponse,
    DowntimeEventListResponse,
    DowntimeSummaryResponse,
    PromoCampaignCreate,
    PromoCampaignResponse,
    PromoCampaignListResponse,
    PromoCampaignEffectivenessResponse,
    KPIResponse,
    OTIFResponse,
    KPIBreakdownResponse,
    SalesMarginResponse,
    ProductionLineResponse,
    ProductionLinesListResponse,
    LineProductivityResponse,
    ScrapPercentageResponse,
    MarginalityResponse,
    CostPerKgResponse,
    EBITDAResponse,
    MarketShareResponse,
    CostBaseCreate,
    CostBaseResponse,
    CostBaseListResponse,
    KPIConfigCreate,
    KPIConfigResponse,
)

router = APIRouter(prefix="/api/production", tags=["Production Analytics"])


async def get_analytics_service(db: AsyncSession = Depends(get_db)):
    """Dependency to get production analytics service."""
    return ProductionAnalyticsService(db)


async def get_batch_input_service(db: AsyncSession = Depends(get_db)):
    """Dependency to get batch input service."""
    gateway = GatewayClient()
    return BatchInputService(db, gateway)


async def get_downtime_event_service(db: AsyncSession = Depends(get_db)):
    """Dependency to get downtime event service."""
    gateway = GatewayClient()
    return DowntimeEventService(db, gateway)


async def get_promo_campaign_service(db: AsyncSession = Depends(get_db)):
    """Dependency to get promo campaign service."""
    gateway = GatewayClient()
    return PromoCampaignService(db, gateway)


async def get_personnel_service(db: AsyncSession = Depends(get_db)):
    """Dependency to get personnel service."""
    gateway = GatewayClient()
    return PersonnelService(db, gateway)


async def get_cost_base_service(db: AsyncSession = Depends(get_db)):
    """Dependency to get cost base service."""
    return CostBaseService()


# ============ KPI Endpoints ============

@router.get("/kpi", response_model=KPIResponse)
async def get_kpi(
    from_date: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    production_line_id: Optional[str] = Query(None, description="Filter by production line UUID"),
    granularity: Literal["day", "week", "month"] = Query("day", description="Trend granularity"),
    compare_with_previous: bool = Query(False, description="Include comparison with previous period"),
    service: ProductionAnalyticsService = Depends(get_analytics_service)
):
    """
    Get enriched KPI with targets, trends, and optional comparison.

    Returns: totalOutput, defectRate, oeeEstimate, targets, trend, changePercent.
    """
    return await service.get_kpi(from_date, to_date, production_line_id, granularity, compare_with_previous)


@router.get("/kpi/otif", response_model=OTIFResponse)
async def get_otif(
    from_date: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    production_line_id: Optional[str] = Query(None, description="Filter by production line UUID"),
    service: ProductionAnalyticsService = Depends(get_analytics_service)
):
    """
    Get OTIF (On-Time In-Full) metrics.

    OTIF = orders that were both on-time AND in-full / total orders.
    """
    return await service.get_otif(from_date, to_date, production_line_id)


@router.get("/kpi/breakdown", response_model=KPIBreakdownResponse)
async def get_kpi_breakdown(
    from_date: date = Query(..., description="Period start date"),
    to_date: date = Query(..., description="Period end date"),
    group_by: Literal["productionLine", "product", "division"] = Query("productionLine", description="Group by dimension"),
    metric: Literal["oeeEstimate", "defectRate", "lineThroughput", "otifRate"] = Query("oeeEstimate", description="Metric to break down"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    service: ProductionAnalyticsService = Depends(get_analytics_service)
):
    """
    Get KPI breakdown (drill-down) by production line, product, or division.

    Useful for: comparing line performance, finding bottlenecks, division analysis.
    """
    return await service.get_kpi_breakdown(from_date, to_date, group_by, metric, offset, limit)


# ============ Sales Endpoints ============

@router.get("/sales/margin", response_model=SalesMarginResponse)
async def get_sales_margin(
    from_date: date = Query(..., description="Period start date"),
    to_date: date = Query(..., description="Period end date"),
    product_id: Optional[str] = Query(None, description="Filter by product UUID"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    service: ProductionAnalyticsService = Depends(get_analytics_service)
):
    """
    Get sales margin by product.

    Returns: product revenue, cost, margin, margin %, margin per unit.
    Note: Cost is estimated at 50% of revenue (configurable).
    """
    return await service.get_sales_margin(from_date, to_date, product_id, offset, limit)


# ============ Batch Inputs ============

@router.post("/batch-inputs", response_model=BatchInputResponse)
async def create_batch_input(
    payload: BatchInputCreate,
    service: BatchInputService = Depends(get_batch_input_service)
):
    """Create a new batch input record."""
    return await service.create_batch_input(
        payload.order_id,
        payload.product_id,
        payload.quantity,
        payload.input_date
    )


@router.get("/batch-inputs", response_model=BatchInputListResponse)
async def list_batch_inputs(
    order_id: Optional[str] = Query(None, description="Filter by order UUID"),
    product_id: Optional[str] = Query(None, description="Filter by product UUID"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    service: BatchInputService = Depends(get_batch_input_service)
):
    """Get batch inputs (raw material intake records)."""
    return await service.get_batch_inputs(
        UUID(order_id) if order_id else None,
        UUID(product_id) if product_id else None,
        offset,
        limit
    )


@router.get("/batch-inputs/yield", response_model=YieldResponse)
async def get_batch_yield(
    order_id: str = Query(..., description="Order UUID"),
    service: BatchInputService = Depends(get_batch_input_service)
):
    """
    Get yield ratio (input to output) for an order.

    Yield % = (total output / total input) * 100.
    KPI: "Выход масла с тонны семян".
    """
    return await service.get_yield_ratio(UUID(order_id))


# ============ Downtime Events ============

@router.post("/downtime-events", response_model=DowntimeEventResponse)
async def create_downtime_event(
    payload: DowntimeEventCreate,
    service: DowntimeEventService = Depends(get_downtime_event_service)
):
    """Create a new downtime event."""
    return await service.create_downtime_event(
        payload.production_line_id,
        payload.reason,
        payload.category,
        payload.started_at,
        payload.ended_at,
        payload.duration_minutes
    )


@router.get("/downtime-events", response_model=DowntimeEventListResponse)
async def list_downtime_events(
    from_date: Optional[date] = Query(None, description="Period start date"),
    to_date: Optional[date] = Query(None, description="Period end date"),
    production_line_id: Optional[str] = Query(None, description="Filter by production line UUID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    service: DowntimeEventService = Depends(get_downtime_event_service)
):
    """Get equipment downtime events."""
    return await service.get_downtime_events(
        from_date,
        to_date,
        UUID(production_line_id) if production_line_id else None,
        category,
        offset,
        limit
    )


@router.get("/downtime-events/summary", response_model=DowntimeSummaryResponse)
async def get_downtime_summary(
    from_date: Optional[date] = Query(None, description="Period start date"),
    to_date: Optional[date] = Query(None, description="Period end date"),
    service: DowntimeEventService = Depends(get_downtime_event_service)
):
    """
    Get aggregated downtime summary by category.

    Categories: PLANNED_MAINTENANCE, UNPLANNED_BREAKDOWN, QUALITY_ISSUE, MATERIAL_SHORTAGE, OTHER.
    KPI: "Время простоев".
    """
    return await service.get_downtime_summary(from_date, to_date)


# ============ Promo Campaigns ============

@router.post("/promo-campaigns", response_model=PromoCampaignResponse)
async def create_promo_campaign(
    payload: PromoCampaignCreate,
    service: PromoCampaignService = Depends(get_promo_campaign_service)
):
    """Create a new promotional campaign."""
    return await service.create_promo_campaign(
        payload.name,
        payload.description,
        payload.channel,
        payload.product_id,
        payload.discount_percent,
        payload.start_date,
        payload.end_date,
        payload.budget
    )


@router.get("/promo-campaigns", response_model=PromoCampaignListResponse)
async def list_promo_campaigns(
    from_date: Optional[date] = Query(None, description="Period start date"),
    to_date: Optional[date] = Query(None, description="Period end date"),
    channel: Optional[str] = Query(None, description="Filter by channel (DIRECT, DISTRIBUTOR, RETAIL, ONLINE)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    service: PromoCampaignService = Depends(get_promo_campaign_service)
):
    """Get promotional campaigns."""
    return await service.get_promo_campaigns(from_date, to_date, channel, offset, limit)


@router.get("/promo-campaigns/{campaign_id}/effectiveness", response_model=PromoCampaignEffectivenessResponse)
async def get_campaign_effectiveness(
    campaign_id: str = Path(..., description="Campaign UUID"),
    service: PromoCampaignService = Depends(get_promo_campaign_service)
):
    """
    Get campaign effectiveness metrics.

    Returns: ROI, uplift, cost per uplift unit.
    KPI: "Эффективность промо-акций".
    """
    return await service.get_effectiveness(UUID(campaign_id))


# ============ Phase 2 KPI Endpoints ============

@router.get("/kpi/line-productivity", response_model=LineProductivityResponse)
async def get_line_productivity(
    from_date: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    production_line_id: Optional[str] = Query(None, description="Filter by production line UUID"),
    service: ProductionAnalyticsService = Depends(get_analytics_service)
):
    """
    Get line productivity (tonnes/hour).
    KPI: "Производительность линии (т/сут)".
    """
    return await service.get_line_productivity(from_date, to_date, production_line_id)


@router.get("/kpi/scrap-percentage", response_model=ScrapPercentageResponse)
async def get_scrap_percentage(
    from_date: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    product_id: Optional[str] = Query(None, description="Filter by product UUID"),
    service: ProductionAnalyticsService = Depends(get_analytics_service)
):
    """
    Get scrap percentage (quality defects).
    KPI: "Процент брака ≤ 1,5%".
    """
    return await service.get_scrap_percentage(from_date, to_date, product_id)


# ============ Phase 3 KPI Endpoints ============

@router.get("/kpi/marginality", response_model=MarginalityResponse)
async def get_marginality(
    from_date: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    product_id: Optional[str] = Query(None, description="Filter by product UUID"),
    service: ProductionAnalyticsService = Depends(get_analytics_service)
):
    """
    Get marginality (profit margin %).
    KPI: "Маржинальность (%) 18%".
    """
    return await service.get_marginality(from_date, to_date, product_id)


@router.get("/kpi/cost-per-kg", response_model=CostPerKgResponse)
async def get_cost_per_kg(
    from_date: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    product_id: Optional[str] = Query(None, description="Filter by product UUID"),
    service: ProductionAnalyticsService = Depends(get_analytics_service)
):
    """
    Get cost per kg (COGS per unit).
    KPI: "Себестоимость продукции (руб./кг)".
    """
    return await service.get_cost_per_kg(from_date, to_date, product_id)


@router.get("/kpi/ebitda", response_model=EBITDAResponse)
async def get_ebitda(
    from_date: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    service: ProductionAnalyticsService = Depends(get_analytics_service)
):
    """
    Get EBITDA (simplified: Revenue - Operating Costs).
    KPI: "EBITDA (млн руб.)".
    """
    return await service.get_ebitda(from_date, to_date)


@router.get("/kpi/market-share", response_model=MarketShareResponse)
async def get_market_share(
    from_date: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    service: ProductionAnalyticsService = Depends(get_analytics_service)
):
    """
    Get market share % (requires admin-configured market volume).
    KPI: "Доля рынка (%)".
    """
    return await service.get_market_share(from_date, to_date)


# ============ Cost Base Management ============

@router.post("/cost-bases", response_model=CostBaseResponse, status_code=201)
async def create_cost_base(
    payload: CostBaseCreate,
    db: AsyncSession = Depends(get_db),
    service: CostBaseService = Depends(get_cost_base_service)
):
    """
    Create or update a cost base for a product.
    Admin endpoint for setting product costs.
    """
    return await service.create_or_update_cost_base(
        db,
        payload.product_id,
        payload.raw_material_cost,
        payload.labor_cost_per_hour,
        payload.depreciation_monthly,
        payload.period_from,
        payload.period_to,
    )


@router.get("/cost-bases", response_model=CostBaseListResponse)
async def list_cost_bases(
    product_id: Optional[str] = Query(None, description="Filter by product UUID"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    db: AsyncSession = Depends(get_db),
    service: CostBaseService = Depends(get_cost_base_service)
):
    """
    Get all cost bases (paginated).
    """
    return await service.get_all_cost_bases(db, product_id, offset, limit)


# ============ KPI Configuration (Admin) ============

@router.post("/kpi-config", response_model=KPIConfigResponse, status_code=201)
async def set_kpi_config(
    payload: KPIConfigCreate,
    db: AsyncSession = Depends(get_db),
    service: CostBaseService = Depends(get_cost_base_service)
):
    """
    Set or update a KPI configuration value.
    Admin endpoint for configurable KPIs (EBITDA target, market volume, etc.).
    """
    return await service.set_kpi_config(
        db,
        payload.key,
        payload.value,
        payload.description,
        payload.updated_by,
    )


@router.get("/kpi-config/{key}", response_model=KPIConfigResponse)
async def get_kpi_config(
    key: str = Path(..., description="Config key"),
    db: AsyncSession = Depends(get_db),
    service: CostBaseService = Depends(get_cost_base_service)
):
    """
    Get a single KPI configuration value.
    """
    value = await service.get_kpi_config(db, key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Config key '{key}' not found")
    return {
        "id": "",
        "key": key,
        "value": value,
        "description": None,
        "updated_by": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


# ============ Reference Data ============

@router.get("/production-lines", response_model=ProductionLinesListResponse)
async def list_production_lines(
    division: Optional[str] = Query(None, description="Filter by division"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    service: PersonnelService = Depends(get_personnel_service)
):
    """Get production lines (from personnel reference data)."""
    return await service.get_production_lines(division, offset, limit)
