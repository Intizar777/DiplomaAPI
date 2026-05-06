"""
Sensor API routes.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GatewayClient, SensorService
from app.schemas.common import DateRangeParams

router = APIRouter(prefix="/api/v1/sensors", tags=["Sensors"])


async def get_services(db: AsyncSession = Depends(get_db)):
    """Dependency to get Sensor services."""
    gateway = GatewayClient()
    service = SensorService(db, gateway)
    return service


@router.get("/history")
async def get_sensor_history(
    production_line: Optional[str] = Query(None, description="Filter by production line"),
    parameter_name: Optional[str] = Query(None, description="Filter by parameter"),
    date_range: DateRangeParams = Depends(),
    limit: int = Query(500, ge=1, le=5000, description="Max readings to return"),
    service: SensorService = Depends(get_services)
):
    """
    Get sensor readings history for trends.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=1))
    to_date = date_range.date_to or date.today()
    
    return await service.get_sensor_history(
        production_line=production_line,
        parameter_name=parameter_name,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )


@router.get("/alerts")
async def get_sensor_alerts(
    date_range: DateRangeParams = Depends(),
    limit: int = Query(100, ge=1, le=1000, description="Max alerts to return"),
    service: SensorService = Depends(get_services)
):
    """
    Get sensor readings with quality issues (anomalies).
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=7))
    to_date = date_range.date_to or date.today()
    
    return await service.get_sensor_alerts(from_date=from_date, to_date=to_date, limit=limit)


@router.get("/stats")
async def get_sensor_stats(
    production_line: Optional[str] = Query(None, description="Filter by production line"),
    service: SensorService = Depends(get_services)
):
    """
    Get aggregated statistics per parameter per line.
    """
    return await service.get_sensor_stats(production_line=production_line)
