"""
Finance Manager Dashboard router.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.finance_dashboard_service import FinanceManagerDashboardService
from app.schemas.finance_dashboard import (
    GroupByType,
    IntervalType,
    SortBy,
    SalesBreakdownResponse,
    RevenueTrendResponse,
    TopProductsResponse,
)

router = APIRouter(prefix="/api/v1/dashboards/finance", tags=["Finance Manager Dashboard"])


async def get_service(db: AsyncSession = Depends(get_db)) -> FinanceManagerDashboardService:
    """Dependency to inject FinanceManagerDashboardService."""
    return FinanceManagerDashboardService(db)


@router.get("/sales-breakdown", response_model=SalesBreakdownResponse)
async def get_sales_breakdown(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Start of period (YYYY-MM-DD). Defaults to 30 days ago.",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD). Defaults to today.",
    ),
    group_by: GroupByType = Query(
        default=GroupByType.channel,
        description="Dimension to group by: 'channel', 'region', or 'product'.",
    ),
    service: FinanceManagerDashboardService = Depends(get_service),
) -> SalesBreakdownResponse:
    """
    Revenue breakdown by channel, region, or product.

    Reads from AggregatedSales. Groups are ranked descending by total_amount
    and include their share of the grand total.
    """
    return await service.get_sales_breakdown(date_from, date_to, group_by)


@router.get("/revenue-trend", response_model=RevenueTrendResponse)
async def get_revenue_trend(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=90),
        description="Start of period (YYYY-MM-DD). Defaults to 90 days ago.",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD). Defaults to today.",
    ),
    interval: IntervalType = Query(
        default=IntervalType.week,
        description="Aggregation interval: 'day', 'week', or 'month'.",
    ),
    region: Optional[str] = Query(
        default=None,
        description="Filter by region name. Omit for all regions.",
    ),
    channel: Optional[str] = Query(
        default=None,
        description="Filter by sales channel. Omit for all channels.",
    ),
    service: FinanceManagerDashboardService = Depends(get_service),
) -> RevenueTrendResponse:
    """
    Revenue trend by interval with period-over-period growth %.

    Reads from SalesTrends. Includes mom_growth_pct starting from the second data point.
    """
    return await service.get_revenue_trend(date_from, date_to, interval, region, channel)


@router.get("/top-products", response_model=TopProductsResponse)
async def get_top_products(
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Start of period (YYYY-MM-DD). Defaults to 30 days ago.",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD). Defaults to today.",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of products to return (1–50).",
    ),
    sort_by: SortBy = Query(
        default=SortBy.amount,
        description="Sort dimension: 'amount' (revenue) or 'quantity'.",
    ),
    service: FinanceManagerDashboardService = Depends(get_service),
) -> TopProductsResponse:
    """
    Top products ranked by revenue or volume.

    Reads from SaleRecord. amount_share_pct is calculated against the grand total
    across ALL products, not just the top-N returned.
    """
    return await service.get_top_products(date_from, date_to, limit, sort_by)
