from datetime import date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class InventoryProductSummary(BaseModel):
    id: str
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InventoryItem(BaseModel):
    product_id: str
    product_name: Optional[str]
    warehouse_code: str
    lot_number: Optional[str]
    quantity: float
    unit_of_measure: Optional[str]
    last_updated: Optional[str]
    product: Optional[InventoryProductSummary] = None

    model_config = ConfigDict(from_attributes=True)


class InventoryTrendItem(BaseModel):
    date: date
    total_quantity: float

    model_config = ConfigDict(from_attributes=True)


class InventoryCurrentResponse(BaseModel):
    items: List[InventoryItem]
    meta: PaginationMeta
    snapshot_date: Optional[str]
    sort: str = "warehouse_code"
    order: str = "asc"

    model_config = ConfigDict(from_attributes=True)


class InventoryTrendsResponse(BaseModel):
    items: List[InventoryTrendItem]
    product_id: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "product_id": "5d0f1aa4-bc0e-4f2d-8c67-40f4c3f2b7af",
                "items": [
                    {"date": "2026-05-01", "total_quantity": 125.5},
                    {"date": "2026-05-02", "total_quantity": 131.0},
                ],
            }
        },
    )
