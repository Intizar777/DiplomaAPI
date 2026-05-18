"""
Handler for downtime events.
"""
from typing import Optional

import structlog

from app.database import AsyncSessionLocal
from app.messaging.dispatcher import register
from app.messaging.schemas import DowntimeEventRecordedPayload
from app.services.downtime_event_service import DowntimeEventService

logger = structlog.get_logger()


@register("production.downtime-event.recorded.event")
async def handle_downtime_event_recorded(payload: dict, event_id: Optional[str] = None) -> None:
    """Process downtime event recorded event."""
    data = DowntimeEventRecordedPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = DowntimeEventService(db, gateway=None)
        await service.upsert_from_event(data, event_id=event_id)
        logger.info("downtime_event_recorded_handled", id=str(data.id), category=data.category)
