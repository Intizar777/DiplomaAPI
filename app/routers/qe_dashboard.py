"""
Quality Engineer Dashboard router.
"""
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.qe_dashboard_service import QualityEngineerDashboardService
from app.schemas.qe_dashboard import (
    ParameterTrendsResponse,
    BatchAnalysisResponse,
    DefectParetoResponse,
)

router = APIRouter(prefix="/api/v1/dashboards/qe", tags=["Quality Engineer Dashboard"])


async def get_service(db: AsyncSession = Depends(get_db)) -> QualityEngineerDashboardService:
    """Dependency to inject QualityEngineerDashboardService."""
    return QualityEngineerDashboardService(db)


@router.get("/parameter-trends", response_model=ParameterTrendsResponse)
async def get_parameter_trends(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Start of period (YYYY-MM-DD). Defaults to 30 days ago.",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD). Defaults to today.",
    ),
    service: QualityEngineerDashboardService = Depends(get_service),
) -> ParameterTrendsResponse:
    """
    Daily parameter quality trends with spec bands.

    Returns one entry per distinct parameter_name, each with daily
    aggregations (avg value, test count, out-of-spec %) and spec limits.
    """
    return await service.get_parameter_trends(date_from, date_to)


@router.get("/batch-analysis", response_model=BatchAnalysisResponse)
async def get_batch_analysis(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Start of period (YYYY-MM-DD). Defaults to 30 days ago.",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD). Defaults to today.",
    ),
    service: QualityEngineerDashboardService = Depends(get_service),
) -> BatchAnalysisResponse:
    """
    Lots with at least one out-of-spec result, with per-parameter deviation details.

    Only lots that contain deviations are returned. Each lot includes
    production metadata and per-parameter deviation magnitude.
    """
    return await service.get_batch_analysis(date_from, date_to)


@router.get("/defect-pareto", response_model=DefectParetoResponse)
async def get_defect_pareto(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Start of period (YYYY-MM-DD). Defaults to 30 days ago.",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD). Defaults to today.",
    ),
    product_id: Optional[UUID] = Query(
        default=None,
        description="Optional product filter. Omit to include all products.",
    ),
    service: QualityEngineerDashboardService = Depends(get_service),
) -> DefectParetoResponse:
    """
    Defect Pareto chart: parameters ranked by out-of-spec count with cumulative %.

    Use product_id to narrow results to a specific product.
    """
    return await service.get_defect_pareto(date_from, date_to, product_id)
