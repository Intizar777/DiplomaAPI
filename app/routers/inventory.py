"""
Inventory API routes.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GatewayClient, InventoryService
from app.schemas.common import DateRangeParams

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])


async def get_services(db: AsyncSession = Depends(get_db)):
    """Dependency to get Inventory services."""
    gateway = GatewayClient()
    service = InventoryService(db, gateway)
    return service


@router.get("/current")
async def get_current_inventory(
    warehouse_code: Optional[str] = Query(None, description="Filter by warehouse"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    service: InventoryService = Depends(get_services)
):
    """
    Get current inventory (latest snapshot).
    """
    return await service.get_current_inventory(warehouse_code=warehouse_code, product_id=product_id)


@router.get("/trends")
async def get_inventory_trends(
    product_id: str = Query(..., description="Product ID to track"),
    date_range: DateRangeParams = Depends(),
    service: InventoryService = Depends(get_services)
):
    """
    Get inventory trends for a specific product.
    """
    from_date = date_range.date_from or (date.today() - timedelta(days=30))
    to_date = date_range.date_to or date.today()
    
    return await service.get_inventory_trends(product_id=product_id, from_date=from_date, to_date=to_date)
