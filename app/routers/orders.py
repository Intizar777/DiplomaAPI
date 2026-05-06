"""
Orders API routes.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GatewayClient, OrderService
from app.schemas import OrderStatusSummaryResponse, OrderListResponse, OrderDetailResponse
from app.schemas.common import DateRangeParams, PaginationParams

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


async def get_services(db: AsyncSession = Depends(get_db)):
    """Dependency to get order services."""
    gateway = GatewayClient()
    service = OrderService(db, gateway)
    return service


@router.get("/status-summary", response_model=OrderStatusSummaryResponse)
async def get_order_status_summary(
    date_range: DateRangeParams = Depends(),
    production_line: Optional[str] = Query(None, description="Filter by production line"),
    service: OrderService = Depends(get_services)
):
    """
    Get summary of orders grouped by status and production line.
    
    Returns counts for: planned, in_progress, completed, cancelled
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()
    
    return await service.get_status_summary(from_date, to_date, production_line)


@router.get("/list", response_model=OrderListResponse)
async def get_orders_list(
    date_range: DateRangeParams = Depends(),
    status: Optional[str] = Query(None, description="Filter by status (planned, in_progress, completed, cancelled)"),
    production_line: Optional[str] = Query(None, description="Filter by production line"),
    pagination: PaginationParams = Depends(),
    service: OrderService = Depends(get_services)
):
    """
    Get paginated list of production orders.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()
    
    return await service.get_order_list(
        from_date, to_date,
        status=status,
        production_line=production_line,
        page=pagination.page,
        limit=pagination.limit
    )


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order_detail(
    order_id: str,
    service: OrderService = Depends(get_services)
):
    """
    Get detailed information about a specific order.
    """
    order = await service.get_order_detail(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
