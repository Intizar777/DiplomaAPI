"""
Handler for sensor reading events.
"""
from typing import Optional

import structlog

from app.database import AsyncSessionLocal
from app.messaging.dispatcher import register
from app.messaging.schemas import SensorReadingRecordedPayload
from app.services.sensor_service import SensorService

logger = structlog.get_logger()


@register("production.sensor-reading.recorded.event")
async def handle_sensor_reading_recorded(payload: dict, event_id: Optional[str] = None) -> None:
    """Process sensor reading recorded event."""
    data = SensorReadingRecordedPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = SensorService(db, gateway=None)
        await service.upsert_sensor_reading_from_event(data, event_id=event_id)
        logger.info("sensor_reading_recorded_handled", id=str(data.id), device=data.device_id)
