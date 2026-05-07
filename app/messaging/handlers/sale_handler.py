"""
Handler for sale events (recorded).
"""
import structlog

from app.database import AsyncSessionLocal
from app.messaging.dispatcher import register
from app.messaging.schemas import SaleRecordedPayload
from app.services.sales_service import SalesService

logger = structlog.get_logger()


@register("production.sale.recorded.event")
async def handle_sale_recorded(payload: dict, event_id: str = None) -> None:
    """Process sale recorded event."""
    data = SaleRecordedPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = SalesService(db, gateway=None)
        await service.upsert_sale_from_event(data, event_id=event_id)
        logger.info("sale_recorded_event_handled", event_id=str(data.id), amount=data.amount)
