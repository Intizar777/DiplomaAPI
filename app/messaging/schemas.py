"""
Pydantic models for RabbitMQ event envelope and payloads.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    """Standard envelope for all RabbitMQ events."""
    event_id: UUID = Field(alias="event_id")
    event_type: str = Field(alias="event_type")
    timestamp: datetime
    source_service: str = Field(alias="source_service")
    correlation_id: UUID = Field(alias="correlation_id")
    version: str
    payload: dict[str, Any]

    model_config = {"populate_by_name": True}


class ProductEventPayload(BaseModel):
    """Payload for product.created and product.updated events."""
    id: UUID
    code: str
    name: str
    category: str | None = None

    model_config = {"populate_by_name": True}


class OrderCreatedPayload(BaseModel):
    """Payload for order.created event."""
    id: UUID
    external_order_id: str | None = Field(default=None, alias="externalOrderId")
    product_id: UUID = Field(alias="productId")
    status: str

    model_config = {"populate_by_name": True}


class OrderStatusUpdatedPayload(BaseModel):
    """Payload for order.status-updated event."""
    id: UUID
    status: str
    actual_quantity: float | None = Field(default=None, alias="actualQuantity")
    actual_start: datetime | None = Field(default=None, alias="actualStart")
    actual_end: datetime | None = Field(default=None, alias="actualEnd")

    model_config = {"populate_by_name": True}


class OutputRecordedPayload(BaseModel):
    """Payload for output.recorded event."""
    id: UUID
    order_id: UUID = Field(alias="orderId")
    lot_number: str = Field(alias="lotNumber")
    quantity: float

    model_config = {"populate_by_name": True}


class SaleRecordedPayload(BaseModel):
    """Payload for sale.recorded event."""
    id: UUID
    external_id: str | None = Field(default=None, alias="externalId")
    product_id: UUID = Field(alias="productId")
    amount: float
    cost: float | None = Field(default=None, alias="cost")
    channel: str | None = None

    model_config = {"populate_by_name": True}


class InventoryUpdatedPayload(BaseModel):
    """Payload for inventory.updated event."""
    id: UUID
    product_id: UUID = Field(alias="productId")
    warehouse_code: str = Field(alias="warehouseCode")
    quantity: float

    model_config = {"populate_by_name": True}


class QualityResultRecordedPayload(BaseModel):
    """Payload for quality-result.recorded event."""
    id: UUID
    lot_number: str = Field(alias="lotNumber")
    product_id: UUID = Field(alias="productId")
    in_spec: bool = Field(alias="inSpec")
    quality_status: str = Field(alias="qualityStatus")

    model_config = {"populate_by_name": True}
