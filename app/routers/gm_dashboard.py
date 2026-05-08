"""
Group Manager Strategic Dashboard router.
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.gm_dashboard_service import GroupManagerDashboardService
from app.schemas.gm_dashboard import (
    OEESummaryResponse,
    PlanExecutionResponse,
    DowntimeRankingResponse,
)

router = APIRouter(prefix="/api/v1/dashboards/gm", tags=["Group Manager Dashboard"])


async def get_service(db: AsyncSession = Depends(get_db)) -> GroupManagerDashboardService:
    """Dependency to inject GroupManagerDashboardService."""
    return GroupManagerDashboardService(db)


@router.get("/oee-summary", response_model=OEESummaryResponse)
async def get_oee_summary(
    period_days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Lookback window in days. Typical values: 7, 30, 90.",
    ),
    service: GroupManagerDashboardService = Depends(get_service),
) -> OEESummaryResponse:
    """
    OEE summary by production line for the Group Manager.

    Returns each production line ranked best-to-worst by average OEE,
    with trend data points and comparison against the 75% target.
    NULL production_line represents the all-lines aggregate KPI record.
    """
    return await service.get_oee_summary(period_days)


@router.get("/plan-execution", response_model=PlanExecutionResponse)
async def get_plan_execution(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Start of period (YYYY-MM-DD). Defaults to 30 days ago.",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD). Defaults to today.",
    ),
    service: GroupManagerDashboardService = Depends(get_service),
) -> PlanExecutionResponse:
    """
    Plan vs actual execution by production line.

    Summarises target vs actual quantities, fulfillment percentage,
    and order status breakdown per line for the requested period.
    """
    return await service.get_plan_execution(date_from, date_to)


@router.get("/downtime-ranking", response_model=DowntimeRankingResponse)
async def get_downtime_ranking(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Start of period (YYYY-MM-DD). Defaults to 30 days ago.",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD). Defaults to today.",
    ),
    service: GroupManagerDashboardService = Depends(get_service),
) -> DowntimeRankingResponse:
    """
    Pareto ranking of production lines by total downtime/delay hours.

    Only considers completed orders with both planned_end and actual_end set.
    Lines are ranked worst-first (highest total_delay_hours first).
    """
    return await service.get_downtime_ranking(date_from, date_to)
