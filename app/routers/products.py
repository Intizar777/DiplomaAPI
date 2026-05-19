"""
Product API routes.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GatewayClient, ProductService
from app.schemas.products import ProductsListResponse, ProductDetailResponse

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


async def get_services(db: AsyncSession = Depends(get_db)):
    """Dependency to get Product services."""
    gateway = GatewayClient()
    service = ProductService(db, gateway)
    return service


@router.get("", response_model=ProductsListResponse)
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    service: ProductService = Depends(get_services)
):
    """
    Get products list with optional filters.
    """
    from app.schemas.products import ProductListItem
    from app.schemas.common import PaginationMeta

    products = await service.get_products(category, brand)
    return ProductsListResponse(
        items=[
            ProductListItem(
                id=str(p.id),
                code=str(p.code) if p.code is not None else "",
                name=str(p.name) if p.name is not None else "",
                category=str(p.category) if p.category is not None else None,
                brand=str(p.brand) if p.brand is not None else None,
                unit_of_measure_id=str(p.unit_of_measure_id) if p.unit_of_measure_id else None,
                shelf_life_days=int(p.shelf_life_days) if p.shelf_life_days is not None else None,
                requires_quality_check=bool(p.requires_quality_check) if p.requires_quality_check is not None else False,
            )
            for p in products
        ],
        meta=PaginationMeta(),
        sort="name",
        order="asc"
    )


@router.get("/{product_id}", response_model=ProductDetailResponse)
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

    return ProductDetailResponse(
        id=str(product.id),
        code=str(product.code) if product.code is not None else "",
        name=str(product.name) if product.name is not None else "",
        category=str(product.category) if product.category is not None else None,
        brand=str(product.brand) if product.brand is not None else None,
        unit_of_measure=str(product.unit_of_measure) if product.unit_of_measure is not None else None,
        shelf_life_days=int(product.shelf_life_days) if product.shelf_life_days is not None else None,
        requires_quality_check=bool(product.requires_quality_check) if product.requires_quality_check is not None else False,
    )
