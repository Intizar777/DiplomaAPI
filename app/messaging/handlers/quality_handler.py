"""
Handler for quality events (result recorded).
"""
import structlog

from app.database import AsyncSessionLocal
from app.messaging.dispatcher import register
from app.messaging.schemas import QualityResultRecordedPayload
from app.services.quality_service import QualityService

logger = structlog.get_logger()


@register("production.quality-result.recorded.event")
async def handle_quality_result_recorded(payload: dict, event_id: str = None) -> None:
    """Process quality result recorded event."""
    data = QualityResultRecordedPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = QualityService(db, gateway=None)
        await service.upsert_from_event(data, event_id=event_id)
        logger.info("quality_result_recorded_event_handled", event_id=str(data.id), lot_number=data.lot_number)
