"""
Handler for product events (created, updated).
"""
import structlog

from app.database import AsyncSessionLocal
from app.messaging.dispatcher import register
from app.messaging.schemas import ProductEventPayload
from app.services.product_service import ProductService

logger = structlog.get_logger()


@register("production.product.created.event")
@register("production.product.updated.event")
async def handle_product_event(payload: dict, event_id: str = None) -> None:
    """Process product created/updated event."""
    data = ProductEventPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = ProductService(db, gateway=None)
        await service.upsert_from_event(data, event_id=event_id)
        logger.info("product_event_handled", event_id=str(data.id), code=data.code)
