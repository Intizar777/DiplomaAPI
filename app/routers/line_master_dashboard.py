"""
Line Master Dashboard API routes.
Endpoints for shift-level production and quality dashboards.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import LineMasterDashboardService
from app.schemas import (
    ShiftProgressResponse,
    ShiftComparisonResponse,
    DefectSummaryResponse,
)

router = APIRouter(prefix="/api/v1/dashboards/line-master", tags=["Line Master Dashboard"])


async def get_service(db: AsyncSession = Depends(get_db)) -> LineMasterDashboardService:
    """Dependency to inject LineMasterDashboardService."""
    return LineMasterDashboardService(db)


@router.get("/shift-progress", response_model=ShiftProgressResponse)
async def get_shift_progress(
    production_date: date = Query(
        default_factory=date.today,
        description="Production date (YYYY-MM-DD). Defaults to today.",
    ),
    service: LineMasterDashboardService = Depends(get_service),
) -> ShiftProgressResponse:
    """
    Get production progress for all shifts on a given date.

    Returns:
    - Total quantity produced per shift
    - Number of approved vs defective lots
    - Defect rate (%) per shift

    Use this endpoint to monitor real-time shift performance.
    """
    return await service.get_shift_progress(production_date)


@router.get("/shift-comparison", response_model=ShiftComparisonResponse)
async def get_shift_comparison(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=7),
        description="Start of period (YYYY-MM-DD). Defaults to 7 days ago.",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD). Defaults to today.",
    ),
    service: LineMasterDashboardService = Depends(get_service),
) -> ShiftComparisonResponse:
    """
    Compare shift performance across a date range.

    Returns:
    - Production quantity and lot count per shift
    - Defect count for trend analysis

    Use this endpoint to compare shifts between days and identify patterns.
    """
    return await service.get_shift_comparison(date_from, date_to)


@router.get("/defect-summary", response_model=DefectSummaryResponse)
async def get_defect_summary(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=7),
        description="Start of period (YYYY-MM-DD). Defaults to 7 days ago.",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD). Defaults to today.",
    ),
    service: LineMasterDashboardService = Depends(get_service),
) -> DefectSummaryResponse:
    """
    Get summary of quality defects by parameter over a period.

    Returns:
    - Defect breakdown by quality parameter (acidity, moisture, etc)
    - Total tests and failure rate (%) per parameter
    - Sorted by failure frequency (highest first)

    Use this endpoint to identify which quality parameters need attention.
    """
    return await service.get_defect_summary(date_from, date_to)
