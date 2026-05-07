"""
Handler for output events (recorded).
"""
import structlog

from app.database import AsyncSessionLocal
from app.messaging.dispatcher import register
from app.messaging.schemas import OutputRecordedPayload
from app.services.output_service import OutputService

logger = structlog.get_logger()


@register("production.output.recorded.event")
async def handle_output_recorded(payload: dict, event_id: str = None) -> None:
    """Process output recorded event."""
    data = OutputRecordedPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = OutputService(db, gateway=None)
        await service.upsert_from_event(data, event_id=event_id)
        logger.info("output_recorded_event_handled", event_id=str(data.id), lot_number=data.lot_number)
