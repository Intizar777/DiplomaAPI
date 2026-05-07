"""
Handler for inventory events (updated).
"""
import structlog

from app.database import AsyncSessionLocal
from app.messaging.dispatcher import register
from app.messaging.schemas import InventoryUpdatedPayload
from app.services.inventory_service import InventoryService

logger = structlog.get_logger()


@register("production.inventory.updated.event")
async def handle_inventory_updated(payload: dict, event_id: str = None) -> None:
    """Process inventory updated event."""
    data = InventoryUpdatedPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = InventoryService(db, gateway=None)
        await service.upsert_from_event(data, event_id=event_id)
        logger.info("inventory_updated_event_handled", event_id=str(data.id), warehouse=data.warehouse_code)
