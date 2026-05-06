"""
Output API routes.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GatewayClient, OutputService
from app.schemas.common import DateRangeParams

router = APIRouter(prefix="/api/v1/output", tags=["Output"])


async def get_services(db: AsyncSession = Depends(get_db)):
    """Dependency to get Output services."""
    gateway = GatewayClient()
    service = OutputService(db, gateway)
    return service


@router.get("/summary")
async def get_output_summary(
    date_range: DateRangeParams = Depends(),
    group_by: str = Query("day", description="Group by: day, shift"),
    service: OutputService = Depends(get_services)
):
    """
    Get output summary aggregated by day/shift.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=7))
    to_date = date_range.date_to or date.today()
    
    return await service.get_output_summary(from_date, to_date, group_by)


@router.get("/by-shift")
async def get_output_by_shift(
    date_range: DateRangeParams = Depends(),
    service: OutputService = Depends(get_services)
):
    """
    Get output grouped by shift for line chart.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=7))
    to_date = date_range.date_to or date.today()
    
    return await service.get_output_by_shift(from_date, to_date)
