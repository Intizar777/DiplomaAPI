from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class ProductInventorySummary(BaseModel):
    total_quantity: float
    lots_count: int
    warehouse_count: int
    snapshot_date: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ProductListItem(BaseModel):
    id: str
    code: str
    name: str
    category: Optional[str]
    brand: Optional[str]
    unit_of_measure_id: Optional[str]
    shelf_life_days: Optional[int]
    requires_quality_check: bool
    inventory_summary: Optional[ProductInventorySummary] = None

    model_config = ConfigDict(from_attributes=True)


class ProductsListResponse(BaseModel):
    items: List[ProductListItem]
    meta: PaginationMeta
    sort: str = "name"
    order: str = "asc"

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(BaseModel):
    id: str
    code: str
    name: str
    category: Optional[str]
    brand: Optional[str]
    unit_of_measure: Optional[str]
    shelf_life_days: Optional[int]
    requires_quality_check: bool
    inventory_summary: Optional[ProductInventorySummary] = None

    model_config = ConfigDict(from_attributes=True)
