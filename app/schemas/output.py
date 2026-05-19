from datetime import date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta  # type: ignore[attr-defined]


class OutputSummaryItem(BaseModel):
    date: date
    shift: Optional[str]
    total_quantity: float
    lot_count: int
    approved_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class OutputListResponse(BaseModel):
    items: List[OutputSummaryItem]
    meta: Optional[PaginationMeta] = None
    period_from: date
    period_to: date
    group_by: Optional[str] = None
    sort: str = "date"
    order: str = "asc"

    model_config = ConfigDict(from_attributes=True)
