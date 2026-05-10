"""
Orders API routes.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GatewayClient, OrderService
from app.schemas import (
    OrderStatusSummaryResponse,
    OrderListResponse,
    OrderDetailResponse,
    PlanExecutionResponse,
    DowntimeResponse,
)
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


@router.get("/plan-execution", response_model=PlanExecutionResponse)
async def get_plan_execution(
    start_date: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Start of period (YYYY-MM-DD).",
    ),
    end_date: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD).",
    ),
    service: OrderService = Depends(get_services),
):
    """
    Plan vs actual execution by production line.

    Returns target/actual quantities, fulfillment % and order status counts per line,
    including overdue orders (past planned_end and not completed, or completed late).
    """
    return await service.get_plan_execution_summary(start_date, end_date)


@router.get("/downtime", response_model=DowntimeResponse)
async def get_downtime(
    start_date: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Start of period (YYYY-MM-DD).",
    ),
    end_date: date = Query(
        default_factory=date.today,
        description="End of period (YYYY-MM-DD).",
    ),
    service: OrderService = Depends(get_services),
):
    """
    Pareto ranking of production lines by total delay hours.

    Delay = actual_end - planned_end for completed orders where actual_end > planned_end.
    Lines sorted worst-first with cumulative percentage for Pareto chart.
    """
    return await service.get_downtime_summary(start_date, end_date)


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
