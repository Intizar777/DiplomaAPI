"""
Handler for batch-input events.
"""
from typing import Optional

import structlog

from app.database import AsyncSessionLocal
from app.messaging.dispatcher import register
from app.messaging.schemas import BatchInputRecordedPayload
from app.services.batch_input_service import BatchInputService

logger = structlog.get_logger()


@register("production.batch-input.recorded.event")
async def handle_batch_input_recorded(payload: dict, event_id: Optional[str] = None) -> None:
    """Process batch input recorded event."""
    data = BatchInputRecordedPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = BatchInputService(db, gateway=None)
        await service.upsert_from_event(data, event_id=event_id)
        logger.info("batch_input_recorded_event_handled", id=str(data.id))
