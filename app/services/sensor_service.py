"""
Sensor business logic service.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict
from uuid import UUID

from sqlalchemy import select, func, desc, and_, Integer, outerjoin
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SensorReading, Sensor, SensorParameter
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
import structlog

logger = structlog.get_logger()


class SensorService:
    """Service for Sensor readings business logic."""

    def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
        self.db = db
        self.gateway = gateway
    
    async def get_sensor_history(
        self,
        production_line_id: Optional[str] = None,
        parameter_name: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 500
    ) -> Dict:
        """Get sensor readings history for trends."""
        query = select(
            SensorReading,
            Sensor.device_id,
            Sensor.production_line_id,
            SensorParameter.name.label("param_name"),
            SensorParameter.unit
        ).outerjoin(
            Sensor, SensorReading.sensor_id == Sensor.id
        ).outerjoin(
            SensorParameter, Sensor.sensor_parameter_id == SensorParameter.id
        ).order_by(desc(SensorReading.recorded_at))

        if production_line_id:
            query = query.where(Sensor.production_line_id == production_line_id)
        if parameter_name:
            query = query.where(SensorParameter.name == parameter_name)
        if from_date:
            query = query.where(SensorReading.recorded_at >= from_date)
        if to_date:
            query = query.where(SensorReading.recorded_at <= to_date)

        query = query.limit(limit)
        result = await self.db.execute(query)
        rows = result.all()

        items = [
            {
                "device_id": row.device_id,
                "production_line_id": str(row.production_line_id) if row.production_line_id else None,
                "parameter_name": row.param_name,
                "value": float(row.SensorReading.value) if row.SensorReading.value else None,
                "unit": row.unit,
                "quality": row.SensorReading.quality,
                "recorded_at": row.SensorReading.recorded_at.isoformat() if row.SensorReading.recorded_at else None,
            }
            for row in rows
        ]

        return {"items": items, "count": len(items)}
    
    async def get_sensor_alerts(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100
    ) -> Dict:
        """Get sensor readings with quality issues (alerts)."""
        query = select(
            SensorReading,
            Sensor.device_id,
            Sensor.production_line_id,
            SensorParameter.name.label("param_name"),
            SensorParameter.unit
        ).outerjoin(
            Sensor, SensorReading.sensor_id == Sensor.id
        ).outerjoin(
            SensorParameter, Sensor.sensor_parameter_id == SensorParameter.id
        ).where(
            SensorReading.quality.in_(["BAD", "DEGRADED"])
        ).order_by(desc(SensorReading.recorded_at))

        if from_date:
            query = query.where(SensorReading.recorded_at >= from_date)
        if to_date:
            query = query.where(SensorReading.recorded_at <= to_date)

        query = query.limit(limit)
        result = await self.db.execute(query)
        rows = result.all()

        items = [
            {
                "device_id": row.device_id,
                "production_line_id": str(row.production_line_id) if row.production_line_id else None,
                "parameter_name": row.param_name,
                "value": float(row.SensorReading.value) if row.SensorReading.value else None,
                "unit": row.unit,
                "quality": row.SensorReading.quality,
                "recorded_at": row.SensorReading.recorded_at.isoformat() if row.SensorReading.recorded_at else None,
            }
            for row in rows
        ]

        return {"items": items, "count": len(items)}
    
    async def get_sensor_stats(
        self,
        production_line_id: Optional[str] = None
    ) -> Dict:
        """Get aggregated statistics per parameter per line."""
        query = select(
            Sensor.production_line_id,
            SensorParameter.name.label("parameter_name"),
            SensorParameter.unit,
            func.avg(SensorReading.value).label("avg_value"),
            func.min(SensorReading.value).label("min_value"),
            func.max(SensorReading.value).label("max_value"),
            func.count(SensorReading.id).label("reading_count"),
            func.sum(func.cast(SensorReading.quality.in_(["BAD", "DEGRADED"]), type_=Integer)).label("alert_count")
        ).outerjoin(
            Sensor, SensorReading.sensor_id == Sensor.id
        ).outerjoin(
            SensorParameter, Sensor.sensor_parameter_id == SensorParameter.id
        ).group_by(
            Sensor.production_line_id,
            SensorParameter.name,
            SensorParameter.unit
        )

        if production_line_id:
            query = query.where(Sensor.production_line_id == production_line_id)

        result = await self.db.execute(query)
        rows = result.all()

        items = [
            {
                "production_line_id": str(row.production_line_id) if row.production_line_id else None,
                "parameter_name": row.parameter_name,
                "unit": row.unit,
                "avg_value": float(row.avg_value) if row.avg_value else None,
                "min_value": float(row.min_value) if row.min_value else None,
                "max_value": float(row.max_value) if row.max_value else None,
                "reading_count": row.reading_count,
                "alert_count": row.alert_count or 0,
            }
            for row in rows
        ]

        return {"items": items}
    
    async def _ensure_sensor_parameter(self, param_id: UUID) -> Optional[UUID]:
        """Ensure a sensor parameter exists by ID. Create stub if missing.

        Used when readings contain only parameter ID, not full parameter data.
        Stub will be updated later by sync_references_task.
        """
        if not param_id:
            return None

        try:
            param_uuid = UUID(str(param_id)) if isinstance(param_id, str) else param_id
        except (ValueError, AttributeError, TypeError):
            logger.warning("invalid_sensor_parameter_id_skipped", raw=param_id)
            return None

        # Check if parameter exists
        existing = await self.db.execute(
            select(SensorParameter).where(SensorParameter.id == param_uuid)
        )
        param = existing.scalar_one_or_none()

        if not param:
            # Create stub parameter with minimum required fields
            # Code limited to 20 chars, use first 8 chars of UUID
            code = f"param_{str(param_uuid)[:8]}"
            param = SensorParameter(
                id=param_uuid,
                code=code,
                name="[Pending sync]",
                unit="[Unknown]",
                description="Stub created during sensor reading sync; will be updated by references sync",
                is_active=True,
            )
            self.db.add(param)
            logger.info("sensor_parameter_stub_created", param_id=param_uuid)

        return param.id

    async def _sync_sensor_parameter(self, param_data: dict) -> Optional[UUID]:
        """Sync a sensor parameter and return its ID."""
        if not param_data:
            return None

        # Handle Pydantic models and dictionaries
        if hasattr(param_data, '__dict__'):  # Pydantic model or dataclass
            param_id_raw = getattr(param_data, 'id', None)
            code = getattr(param_data, 'code', None)
            name = getattr(param_data, 'name', '')
            unit = getattr(param_data, 'unit', '')
            description = getattr(param_data, 'description', None)
            is_active = getattr(param_data, 'isActive', True)
        else:  # Dictionary
            param_id_raw = param_data.get("id")
            code = param_data.get("code")
            name = param_data.get("name", "")
            unit = param_data.get("unit", "")
            description = param_data.get("description")
            is_active = param_data.get("isActive", True)

        try:
            param_id = UUID(param_id_raw) if isinstance(param_id_raw, str) else param_id_raw
        except (ValueError, AttributeError, TypeError):
            logger.warning("invalid_sensor_parameter_id_skipped", raw=param_id_raw)
            return None

        # Try to find existing by code or id
        if code:
            existing = await self.db.execute(
                select(SensorParameter).where(SensorParameter.code == code)
            )
            param = existing.scalar_one_or_none()
        else:
            param = None

        if not param and param_id:
            existing = await self.db.execute(
                select(SensorParameter).where(SensorParameter.id == param_id)
            )
            param = existing.scalar_one_or_none()

        if param:
            param.code = code or param.code
            param.name = name or param.name
            param.unit = unit or param.unit
            param.description = description or param.description
            param.is_active = is_active
        else:
            param = SensorParameter(
                id=param_id,
                code=code or f"param_{param_id}",
                name=name or "",
                unit=unit or "",
                description=description,
                is_active=is_active,
            )
            self.db.add(param)

        return param.id

    async def _sync_sensor(self, sensor_data: dict) -> Optional[UUID]:
        """Sync a sensor device and return its ID.

        Supports two patterns:
        1. Full sync with nested sensorParameter object (from sync_references_task)
        2. Reading sync with separate sensorParameterId UUID (from sync_from_gateway)
        """
        if not sensor_data:
            return None

        sensor_id_raw = sensor_data.get("id")
        try:
            sensor_id = UUID(sensor_id_raw) if isinstance(sensor_id_raw, str) else sensor_id_raw
        except (ValueError, AttributeError, TypeError):
            logger.warning("invalid_sensor_id_skipped", raw=sensor_id_raw)
            return None

        device_id = sensor_data.get("deviceId")

        # Try to find existing by device_id or id
        if device_id:
            existing = await self.db.execute(
                select(Sensor).where(Sensor.device_id == device_id)
            )
            sensor = existing.scalar_one_or_none()
        else:
            sensor = None

        if not sensor and sensor_id:
            existing = await self.db.execute(
                select(Sensor).where(Sensor.id == sensor_id)
            )
            sensor = existing.scalar_one_or_none()

        # Sync sensor parameter from nested object OR use pre-synced parameter ID
        param_id = None
        param_data = sensor_data.get("sensorParameter")
        if param_data:
            param_id = await self._sync_sensor_parameter(param_data)
        else:
            # Pattern 2: Use sensorParameterId if available (from readings sync)
            param_id_raw = sensor_data.get("sensorParameterId")
            if param_id_raw:
                try:
                    param_id = UUID(param_id_raw) if isinstance(param_id_raw, str) else param_id_raw
                except (ValueError, AttributeError, TypeError):
                    pass

        # Parse production_line_id (could be string or UUID)
        prod_line_id = sensor_data.get("productionLineId")
        if prod_line_id:
            prod_line_id = UUID(str(prod_line_id)) if not isinstance(prod_line_id, UUID) else prod_line_id

        if sensor:
            sensor.device_id = device_id or sensor.device_id
            sensor.production_line_id = prod_line_id or sensor.production_line_id
            sensor.sensor_parameter_id = param_id or sensor.sensor_parameter_id
            sensor.is_active = sensor_data.get("isActive", sensor.is_active)
        else:
            sensor = Sensor(
                id=sensor_id,
                device_id=device_id or f"sensor_{sensor_id}",
                production_line_id=prod_line_id,
                sensor_parameter_id=param_id,
                is_active=sensor_data.get("isActive", True),
            )
            self.db.add(sensor)

        return sensor.id

    @track_feature_path(feature_name="sensors.sync_from_gateway", log_result=True)
    async def sync_from_gateway(
        self,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> int:
        """Sync sensor readings from Gateway, including Sensor and SensorParameter hierarchy.

        Flow:
        1. For each reading: ensure SensorParameter exists (create stub if needed)
        2. Build and sync Sensor from reading metadata
        3. Create SensorReading with valid Sensor FK
        """
        logger.info("syncing_sensors_from_gateway", from_date=from_date, to_date=to_date)

        readings_response = await self.gateway.get_sensor_readings(from_date=from_date, to_date=to_date)
        logger.info("sensors_fetched_from_gateway", total_readings=len(readings_response.readings))

        records_processed = 0
        sensors_synced = 0
        parameters_synced = 0
        batch_size = 50
        batch = []
        snapshot_date = datetime.utcnow()

        # Pre-pass: Ensure all SensorParameters exist (avoid autoflush conflicts during Sensor sync)
        for reading_item in readings_response.readings:
            if reading_item.sensorParameterId:
                await self._ensure_sensor_parameter(reading_item.sensorParameterId)
                parameters_synced += 1

        # Commit parameters before syncing sensors to avoid autoflush conflicts
        if parameters_synced > 0:
            await self.db.commit()

        for reading_item in readings_response.readings:
            # Step 1: Get parameter ID (already synced in pre-pass)
            param_id = reading_item.sensorParameterId

            # Step 2: Build and sync Sensor from reading metadata
            sensor_id = None
            if reading_item.sensorId:
                sensor_data = {
                    "id": reading_item.sensorId,
                    "deviceId": reading_item.deviceId,
                    "productionLineId": reading_item.productionLineId,
                    "sensorParameterId": param_id,
                    "isActive": True,
                }
                try:
                    sensor_id = await self._sync_sensor(sensor_data)
                    if sensor_id:
                        sensors_synced += 1
                except Exception as e:
                    logger.error("sensor_sync_error", reading_id=reading_item.id, error=str(e)[:200])
                    continue

            # Step 3: Parse recorded_at
            recorded_at_raw = reading_item.recordedAt
            if isinstance(recorded_at_raw, str):
                try:
                    recorded_at = datetime.fromisoformat(recorded_at_raw.replace("Z", "+00:00"))
                except ValueError:
                    recorded_at = datetime.utcnow()
            elif isinstance(recorded_at_raw, datetime):
                recorded_at = recorded_at_raw
            else:
                recorded_at = datetime.utcnow()

            # Step 4: Create SensorReading (sensor_id guaranteed to exist now)
            if not sensor_id:
                logger.warning("sensor_reading_skipped_no_sensor_id", reading_id=reading_item.id)
                continue

            reading = SensorReading(
                id=reading_item.id,
                sensor_id=sensor_id,
                value=Decimal(str(reading_item.value)) if reading_item.value is not None else None,
                quality=reading_item.quality.lower() if reading_item.quality else None,
                recorded_at=recorded_at,
                snapshot_date=snapshot_date
            )
            batch.append(reading)

            if len(batch) >= batch_size:
                try:
                    for item in batch:
                        await self.db.merge(item)
                    await self.db.commit()
                    records_processed += len(batch)
                    logger.info("sensors_sync_batch", records_processed=records_processed)
                except Exception as e:
                    await self.db.rollback()
                    logger.error("sensors_sync_batch_error", error=str(e)[:200])
                batch = []

        if batch:
            try:
                for item in batch:
                    await self.db.merge(item)
                await self.db.commit()
                records_processed += len(batch)
            except Exception as e:
                await self.db.rollback()
                logger.error("sensors_sync_final_batch_error", error=str(e)[:200])

        log_data_flow(
            source="sensor_service",
            target="database",
            operation="sync_insert",
            records_count=records_processed,
        )
        logger.info(
            "sensors_sync_completed",
            records_processed=records_processed,
            sensors_synced=sensors_synced,
            parameters_synced=parameters_synced,
        )
        return records_processed
