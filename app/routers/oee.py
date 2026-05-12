"""
OEE (Overall Equipment Effectiveness) endpoints.
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.oee import (
    OEESummaryResponse,
    OEELineResponse,
    LineCapacityPlanRequest,
    LineCapacityPlanResponse,
)
from app.services.oee_service import OEEService

router = APIRouter(prefix="/api/v1/oee", tags=["OEE"])
oee_service = OEEService()


@router.get(
    "/summary",
    response_model=OEESummaryResponse,
    summary="Get OEE summary for a period",
    description="Calculate OEE (Overall Equipment Effectiveness) summary across all production lines.",
)
async def get_oee_summary(
    session: AsyncSession = Depends(get_db),
    period_from: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    period_to: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    production_line_id: str | None = Query(None, description="Optional: filter by production line ID"),
) -> OEESummaryResponse:
    """
    Get OEE summary for a specified period.

    Returns OEE metrics for each production line, including:
    - Availability (Planned time - Downtime) / Planned time × 100
    - Performance (Actual output / Planned output) × 100
    - Quality (Accepted lots / Total lots) × 100
    - OEE = Availability × Performance × Quality / 10000

    Query parameters:
    - period_from: Start date (YYYY-MM-DD)
    - period_to: End date (YYYY-MM-DD)
    - production_line_id (optional): Filter by specific line
    """
    if period_from > period_to:
        raise HTTPException(status_code=400, detail="period_from must be <= period_to")

    try:
        return await oee_service.calculate_oee_summary(
            session,
            period_from=period_from,
            period_to=period_to,
            production_line_id=production_line_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/line/{production_line_id}",
    response_model=OEELineResponse,
    summary="Get OEE for a specific production line",
)
async def get_oee_for_line(
    production_line_id: str,
    session: AsyncSession = Depends(get_db),
    period_from: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    period_to: date = Query(..., description="Period end date (YYYY-MM-DD)"),
) -> OEELineResponse:
    """Get OEE metrics for a specific production line over a period."""
    if period_from > period_to:
        raise HTTPException(status_code=400, detail="period_from must be <= period_to")

    try:
        return await oee_service.calculate_oee_for_line(
            session,
            production_line_id=production_line_id,
            period_from=period_from,
            period_to=period_to,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/today",
    response_model=OEESummaryResponse,
    summary="Get OEE for today",
)
async def get_oee_today(
    session: AsyncSession = Depends(get_db),
) -> OEESummaryResponse:
    """Get OEE metrics for today (last 24 hours)."""
    today = date.today()
    return await oee_service.calculate_oee_summary(
        session,
        period_from=today,
        period_to=today,
    )


@router.get(
    "/this-week",
    response_model=OEESummaryResponse,
    summary="Get OEE for this week",
)
async def get_oee_this_week(
    session: AsyncSession = Depends(get_db),
) -> OEESummaryResponse:
    """Get OEE metrics for current week (Mon-Sun)."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return await oee_service.calculate_oee_summary(
        session,
        period_from=monday,
        period_to=sunday,
    )


@router.get(
    "/this-month",
    response_model=OEESummaryResponse,
    summary="Get OEE for this month",
)
async def get_oee_this_month(
    session: AsyncSession = Depends(get_db),
) -> OEESummaryResponse:
    """Get OEE metrics for current month."""
    today = date.today()
    first_day = date(today.year, today.month, 1)
    if today.month == 12:
        last_day = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(today.year, today.month + 1, 1) - timedelta(days=1)
    return await oee_service.calculate_oee_summary(
        session,
        period_from=first_day,
        period_to=last_day,
    )


@router.post(
    "/capacity-plan",
    response_model=LineCapacityPlanResponse,
    summary="Set production line capacity plan",
    status_code=201,
)
async def create_capacity_plan(
    request: LineCapacityPlanRequest,
    session: AsyncSession = Depends(get_db),
) -> LineCapacityPlanResponse:
    """
    Create or update capacity plan for a production line.

    Used to set planned working hours and OEE target for OEE calculations.
    """
    return await oee_service.set_capacity_plan(
        session,
        production_line_id=request.production_line_id,
        planned_hours_per_day=request.planned_hours_per_day,
        target_oee_percent=request.target_oee_percent,
        period_from=request.period_from,
        period_to=request.period_to,
    )
