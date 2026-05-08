"""
KPI API routes.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GatewayClient, KPIService
from app.schemas import KPICurrentResponse, KPIHistoryResponse, KPICompareResponse
from app.schemas.common import DateRangeParams

router = APIRouter(prefix="/api/v1/kpi", tags=["KPI"])


async def get_services(db: AsyncSession = Depends(get_db)):
    """Dependency to get KPI services."""
    gateway = GatewayClient()
    service = KPIService(db, gateway)
    return service


@router.get("/current", response_model=KPICurrentResponse)
async def get_current_kpi(
    production_line: Optional[str] = Query(None, description="Filter by production line"),
    service: KPIService = Depends(get_services)
):
    """
    Get current KPI metrics (most recent aggregated data).
    """
    return await service.get_current_kpi(production_line)


@router.get("/history", response_model=KPIHistoryResponse)
async def get_kpi_history(
    date_range: DateRangeParams = Depends(),
    production_line: Optional[str] = Query(None, description="Filter by production line"),
    service: KPIService = Depends(get_services)
):
    """
    Get KPI history for a date range.
    """
    # Default to last 30 days if not specified
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()
    
    return await service.get_kpi_history(from_date, to_date, production_line)


@router.get("/all", response_model=KPIHistoryResponse)
async def get_all_kpi(
    production_line: Optional[str] = Query(None, description="Filter by production line"),
    service: KPIService = Depends(get_services)
):
    """
    Get all KPI records (no date filter).
    Useful for verification and debugging.
    """
    return await service.get_all_kpi(production_line)


@router.get("/compare", response_model=KPICompareResponse)
async def compare_kpi(
    period1_from: date = Query(..., description="First period start date"),
    period1_to: date = Query(..., description="First period end date"),
    period2_from: date = Query(..., description="Second period start date"),
    period2_to: date = Query(..., description="Second period end date"),
    service: KPIService = Depends(get_services)
):
    """
    Compare KPI between two periods.

    Example: Compare current month vs previous month
    """
    return await service.compare_kpi_periods(
        period1_from, period1_to,
        period2_from, period2_to
    )


@router.get("/per-line/current", response_model=KPIHistoryResponse)
async def get_kpi_per_line_current(
    service: KPIService = Depends(get_services)
):
    """
    Get current KPI for all production lines (most recent data).
    """
    return await service.get_all_kpi(production_line=None)


@router.get("/per-line/history", response_model=KPIHistoryResponse)
async def get_kpi_per_line_history(
    date_range: DateRangeParams = Depends(),
    production_line: Optional[str] = Query(None, description="Filter by specific production line code"),
    service: KPIService = Depends(get_services)
):
    """
    Get KPI history by production line for a date range.
    Omit production_line parameter to get data for all lines.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()

    return await service.get_kpi_history(from_date, to_date, production_line)
