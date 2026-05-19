from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta  # type: ignore[attr-defined]


class SensorReadingItem(BaseModel):
    device_id: Optional[str]
    production_line_id: Optional[str]
    parameter_name: Optional[str]
    value: Optional[float]
    unit: Optional[str]
    quality: Optional[str]
    recorded_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class SensorReadingsListResponse(BaseModel):
    items: List[SensorReadingItem]
    meta: Optional[PaginationMeta] = None
    next_cursor: Optional[str] = None
    has_more: Optional[bool] = None
    sort: str = "recorded_at"
    order: str = "desc"

    model_config = ConfigDict(from_attributes=True)


class SensorStatsItem(BaseModel):
    production_line_id: Optional[str]
    line_name: Optional[str]
    parameter_name: Optional[str]
    unit: Optional[str]
    avg_value: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]
    reading_count: int
    alert_count: int

    model_config = ConfigDict(from_attributes=True)


class SensorStatsResponse(BaseModel):
    items: List[SensorStatsItem]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "production_line_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "line_name": "Линия А",
                        "parameter_name": "temperature",
                        "unit": "C",
                        "avg_value": 72.5,
                        "min_value": 70.2,
                        "max_value": 74.1,
                        "reading_count": 48,
                        "alert_count": 3,
                    }
                ]
            }
        },
    )
