"""
Handler for order events (created, status-updated).
"""
import structlog

from app.database import AsyncSessionLocal
from app.messaging.dispatcher import register
from app.messaging.schemas import OrderCreatedPayload, OrderStatusUpdatedPayload
from app.services.order_service import OrderService

logger = structlog.get_logger()


@register("production.order.created.event")
async def handle_order_created(payload: dict, event_id: str = None) -> None:
    """Process order created event."""
    data = OrderCreatedPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = OrderService(db, gateway=None)
        await service.upsert_order_from_event(data, event_id=event_id)
        logger.info("order_created_event_handled", event_id=str(data.id))


@register("production.order.status-updated.event")
async def handle_order_status_updated(payload: dict, event_id: str = None) -> None:
    """Process order status updated event."""
    data = OrderStatusUpdatedPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = OrderService(db, gateway=None)
        await service.update_order_status_from_event(data, event_id=event_id)
        logger.info("order_status_updated_event_handled", event_id=str(data.id), status=data.status)
