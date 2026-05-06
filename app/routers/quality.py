"""
Quality API routes.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GatewayClient, QualityService
from app.schemas import QualitySummaryResponse, DefectTrendsResponse, QualityLotsResponse
from app.schemas.common import DateRangeParams

router = APIRouter(prefix="/api/v1/quality", tags=["Quality"])


async def get_services(db: AsyncSession = Depends(get_db)):
    """Dependency to get quality services."""
    gateway = GatewayClient()
    service = QualityService(db, gateway)
    return service


@router.get("/summary", response_model=QualitySummaryResponse)
async def get_quality_summary(
    date_range: DateRangeParams = Depends(),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    service: QualityService = Depends(get_services)
):
    """
    Get quality control summary statistics.
    
    Returns:
    - Average quality score (%)
    - Approved/Rejected/Pending counts
    - Defect rate (%)
    - Stats by quality parameter
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()
    
    return await service.get_quality_summary(from_date, to_date, product_id)


@router.get("/defect-trends", response_model=DefectTrendsResponse)
async def get_defect_trends(
    date_range: DateRangeParams = Depends(),
    service: QualityService = Depends(get_services)
):
    """
    Get defect rate trends over time.
    
    Shows daily defect rates and rejected test counts.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()
    
    return await service.get_defect_trends(from_date, to_date)


@router.get("/lots", response_model=QualityLotsResponse)
async def get_quality_lots(
    date_range: DateRangeParams = Depends(),
    decision: Optional[str] = Query(None, description="Filter by decision (approved, rejected, pending)"),
    service: QualityService = Depends(get_services)
):
    """
    Get quality lots with their test decisions.
    
    Returns list of lots with parameters tested and pass/fail counts.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()
    
    return await service.get_quality_lots(from_date, to_date, decision)
