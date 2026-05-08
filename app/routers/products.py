"""
Product API routes.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GatewayClient, ProductService

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


async def get_services(db: AsyncSession = Depends(get_db)):
    """Dependency to get Product services."""
    gateway = GatewayClient()
    service = ProductService(db, gateway)
    return service


@router.get("")
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    service: ProductService = Depends(get_services)
):
    """
    Get products list with optional filters.
    """
    products = await service.get_products(category, brand)
    return {
        "items": [
            {
                "id": str(p.id),
                "code": p.code,
                "name": p.name,
                "category": p.category,
                "brand": p.brand,
                "unit_of_measure_id": str(p.unit_of_measure_id) if p.unit_of_measure_id else None,
                "shelf_life_days": p.shelf_life_days,
                "requires_quality_check": p.requires_quality_check,
            }
            for p in products
        ],
        "count": len(products)
    }


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    service: ProductService = Depends(get_services)
):
    """
    Get a single product by ID.
    """
    product = await service.get_product(product_id)
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": str(product.id),
        "code": product.code,
        "name": product.name,
        "category": product.category,
        "brand": product.brand,
        "unit_of_measure": product.unit_of_measure,
        "shelf_life_days": product.shelf_life_days,
        "requires_quality_check": product.requires_quality_check,
    }
