"""
Handler for order events (order.changed).
"""
from typing import Optional

import structlog

from app.database import AsyncSessionLocal
from app.messaging.dispatcher import register
from app.messaging.schemas import OrderChangedPayload
from app.services.order_service import OrderService

logger = structlog.get_logger()


@register("production.order.changed.event")
async def handle_order_changed(payload: dict, event_id: Optional[str] = None) -> None:
    """Process order changed event from DailyDataGenerator."""
    data = OrderChangedPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = OrderService(db, gateway=None)
        await service.upsert_order_changed_from_event(data, event_id=event_id)
        logger.info("order_changed_event_handled", order_id=str(data.order_id), status=data.status)
