"""
Sales API routes.
"""
from datetime import date, timedelta
from typing import Optional, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GatewayClient, SalesService
from app.schemas import (
    SalesSummaryResponse,
    SalesTrendsResponse,
    TopProductsResponse,
    SalesRegionsResponse
)
from app.schemas.common import DateRangeParams

router = APIRouter(prefix="/api/v1/sales", tags=["Sales"])


async def get_services(db: AsyncSession = Depends(get_db)):
    """Dependency to get sales services."""
    gateway = GatewayClient()
    service = SalesService(db, gateway)
    return service


@router.get("/summary", response_model=SalesSummaryResponse)
async def get_sales_summary(
    date_range: DateRangeParams = Depends(),
    group_by: Literal["region", "channel", "product"] = Query("region", description="Group by field"),
    service: SalesService = Depends(get_services)
):
    """
    Get aggregated sales summary grouped by region, channel, or product.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()
    
    return await service.get_sales_summary(from_date, to_date, group_by)


@router.get("/trends", response_model=SalesTrendsResponse)
async def get_sales_trends(
    date_range: DateRangeParams = Depends(),
    interval: Literal["day", "week", "month"] = Query("day", description="Trend interval"),
    region: Optional[str] = Query(None, description="Filter by region"),
    channel: Optional[str] = Query(None, description="Filter by sales channel"),
    service: SalesService = Depends(get_services)
):
    """
    Get sales trends over time.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()
    
    return await service.get_sales_trends(from_date, to_date, interval, region, channel)


@router.get("/top-products", response_model=TopProductsResponse)
async def get_top_products(
    date_range: DateRangeParams = Depends(),
    limit: int = Query(10, ge=1, le=100, description="Number of products to return"),
    service: SalesService = Depends(get_services)
):
    """
    Get top selling products by revenue.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()
    
    return await service.get_top_products(from_date, to_date, limit)


@router.get("/regions", response_model=SalesRegionsResponse)
async def get_sales_by_regions(
    date_range: DateRangeParams = Depends(),
    service: SalesService = Depends(get_services)
):
    """
    Get sales breakdown by regions with percentages.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()
    
    return await service.get_sales_by_regions(from_date, to_date)
