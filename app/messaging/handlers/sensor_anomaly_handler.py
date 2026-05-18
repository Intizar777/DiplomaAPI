"""
Handler for sensor anomaly events.
"""
from typing import Optional

import structlog

from app.database import AsyncSessionLocal
from app.messaging.dispatcher import register
from app.messaging.schemas import SensorAnomalyPayload
from app.services.sensor_service import SensorService

logger = structlog.get_logger()


@register("production.sensor.anomaly.event")
async def handle_sensor_anomaly(payload: dict, event_id: Optional[str] = None) -> None:
    """Process sensor anomaly event."""
    data = SensorAnomalyPayload.model_validate(payload)
    async with AsyncSessionLocal() as db:
        service = SensorService(db, gateway=None)
        await service.upsert_anomaly_from_event(data, event_id=event_id)
        logger.info("sensor_anomaly_handled", device=data.device_id, severity=data.severity)
