"""
Sensor business logic service.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.messaging.schemas import SensorReadingRecordedPayload, SensorAnomalyPayload

from sqlalchemy import select, func, desc, and_, Integer, outerjoin
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SensorReading, Sensor, SensorParameter
from app.services.gateway_client import GatewayClient
from app.services.reference_sync import upsert_sensor_parameter
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
            SensorReading.id,
            SensorReading.value,
            SensorReading.quality,
            SensorReading.recorded_at,
            Sensor.device_id,
            Sensor.production_line_id,
            Sensor.parameter_name,
            Sensor.parameter_unit
        ).join(
            Sensor, SensorReading.sensor_id == Sensor.id
        )

        if production_line_id:
            query = query.where(Sensor.production_line_id == UUID(production_line_id))
        if parameter_name:
            query = query.where(Sensor.parameter_name == parameter_name)
        if from_date:
            query = query.where(SensorReading.recorded_at >= from_date)
        if to_date:
            query = query.where(SensorReading.recorded_at <= to_date)

        query = query.order_by(desc(SensorReading.recorded_at)).limit(limit)
        result = await self.db.execute(query)
        rows = result.all()

        items = [
            {
                "device_id": row.device_id,
                "production_line_id": str(row.production_line_id) if row.production_line_id else None,
                "parameter_name": row.parameter_name,
                "value": float(row.value) if row.value else None,
                "unit": row.parameter_unit,
                "quality": row.quality,
                "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
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
            SensorReading.id,
            SensorReading.value,
            SensorReading.quality,
            SensorReading.recorded_at,
            Sensor.device_id,
            Sensor.production_line_id,
            Sensor.parameter_name,
            Sensor.parameter_unit
        ).join(
            Sensor, SensorReading.sensor_id == Sensor.id
        ).where(
            func.lower(SensorReading.quality).in_(["bad", "degraded"])
        )

        if from_date:
            query = query.where(SensorReading.recorded_at >= from_date)
        if to_date:
            query = query.where(SensorReading.recorded_at <= to_date)

        query = query.order_by(desc(SensorReading.recorded_at)).limit(limit)
        result = await self.db.execute(query)
        rows = result.all()

        items = [
            {
                "device_id": row.device_id,
                "production_line_id": str(row.production_line_id) if row.production_line_id else None,
                "parameter_name": row.parameter_name,
                "value": float(row.value) if row.value else None,
                "unit": row.parameter_unit,
                "quality": row.quality,
                "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
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
            Sensor.line_name,
            SensorParameter.name.label("parameter_name"),
            SensorParameter.unit,
            func.avg(SensorReading.value).label("avg_value"),
            func.min(SensorReading.value).label("min_value"),
            func.max(SensorReading.value).label("max_value"),
            func.count(SensorReading.id).label("reading_count"),
            func.sum(func.cast(SensorReading.quality.in_(["bad", "degraded"]), type_=Integer)).label("alert_count")
        ).join(
            Sensor, SensorReading.sensor_id == Sensor.id
        ).join(
            SensorParameter, Sensor.sensor_parameter_id == SensorParameter.id
        ).group_by(
            Sensor.production_line_id,
            Sensor.line_name,
            SensorParameter.name,
            SensorParameter.unit
        )

        if production_line_id:
            query = query.where(Sensor.production_line_id == UUID(production_line_id))

        result = await self.db.execute(query)
        rows = result.all()

        items = [
            {
                "production_line_id": str(row.production_line_id) if row.production_line_id else None,
                "line_name": row.line_name,
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

    async def _sync_sensor(self, sensor_data: dict) -> Optional[UUID]:
        """Upsert a sensor device and return its ID."""
        from app.models.reference import ProductionLine

        if not sensor_data:
            return None

        sensor_id_raw = sensor_data.get("id")
        try:
            sensor_id = UUID(sensor_id_raw) if isinstance(sensor_id_raw, str) else sensor_id_raw
        except (ValueError, AttributeError, TypeError):
            logger.warning("invalid_sensor_id_skipped", raw=sensor_id_raw)
            return None

        device_id = sensor_data.get("deviceId")

        await self.db.flush()

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

        param_id = None
        param_name = None
        param_unit = None
        param_data = sensor_data.get("sensorParameter")
        if param_data:
            param_id = await upsert_sensor_parameter(self.db, param_data)
            param_name = param_data.get("name")
            param_unit = param_data.get("unit")
        else:
            param_id_raw = sensor_data.get("sensorParameterId")
            if param_id_raw:
                try:
                    param_id = UUID(param_id_raw) if isinstance(param_id_raw, str) else param_id_raw
                except (ValueError, AttributeError, TypeError):
                    pass
            # If no param_id, try to get it from SensorParameter table
            if param_id:
                param_result = await self.db.execute(
                    select(SensorParameter.name, SensorParameter.unit).where(SensorParameter.id == param_id)
                )
                param_row = param_result.scalar_one_or_none()
                if param_row:
                    param_name = param_row[0]
                    param_unit = param_row[1]

        prod_line_id = sensor_data.get("productionLineId")
        if prod_line_id:
            prod_line_id = UUID(str(prod_line_id)) if not isinstance(prod_line_id, UUID) else prod_line_id

        line_name = None
        if prod_line_id:
            line_result = await self.db.execute(
                select(ProductionLine.name).where(ProductionLine.id == prod_line_id)
            )
            line_row = line_result.scalar()
            if line_row:
                line_name = line_row

        if sensor:
            sensor.device_id = device_id or sensor.device_id
            sensor.production_line_id = prod_line_id or sensor.production_line_id  # type: ignore[assignment]
            sensor.line_name = line_name or sensor.line_name  # type: ignore[assignment]
            sensor.sensor_parameter_id = param_id or sensor.sensor_parameter_id  # type: ignore[assignment]
            sensor.parameter_name = param_name or sensor.parameter_name
            sensor.parameter_unit = param_unit or sensor.parameter_unit
            sensor.is_active = sensor_data.get("isActive", sensor.is_active)
        else:
            sensor = Sensor(
                id=sensor_id,
                device_id=device_id or f"sensor_{sensor_id}",
                production_line_id=prod_line_id,
                line_name=line_name,
                sensor_parameter_id=param_id,
                parameter_name=param_name,
                parameter_unit=param_unit,
                is_active=sensor_data.get("isActive", True),
            )
            self.db.add(sensor)

        return sensor.id  # type: ignore[return-value]

    @track_feature_path(feature_name="sensors.sync_from_gateway", log_result=True)
    async def sync_from_gateway(
        self,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> int:
        """Sync sensor readings from Gateway, including Sensors and SensorParameters.

        Fetches readings with include=sensorParameter, then:
        1. Extracts unique SensorParameters from embedded data and upserts them
        2. Extracts unique Sensors from readings and upserts them
        3. Creates SensorReading records
        """
        logger.info("syncing_sensors_from_gateway", from_date=from_date, to_date=to_date)

        readings_response = await self.gateway.get_sensor_readings(from_date=from_date, to_date=to_date)  # type: ignore[union-attr]
        logger.info("sensors_fetched_from_gateway", total_readings=len(readings_response.readings))

        records_processed = 0
        sensors_synced = 0
        parameters_synced = 0
        batch_size = 50
        batch = []
        snapshot_date = datetime.utcnow()

        # Phase 1: Extract and upsert unique SensorParameters from embedded data
        seen_params: Dict[UUID, dict] = {}
        for reading_item in readings_response.readings:
            sp = reading_item.sensorParameter
            if sp and sp.id not in seen_params:
                seen_params[sp.id] = {"id": str(sp.id), "name": sp.name, "unit": sp.unit}

        for param_id, param_data in seen_params.items():
            await upsert_sensor_parameter(self.db, param_data)
            parameters_synced += 1

        if parameters_synced > 0:
            await self.db.commit()
            logger.info("sensor_parameters_synced", count=parameters_synced)

        # Phase 2: Extract and upsert unique Sensors from readings
        seen_sensors: Dict[UUID, dict] = {}
        for reading_item in readings_response.readings:
            sid = reading_item.sensorId
            if sid and sid not in seen_sensors:
                seen_sensors[sid] = {
                    "id": str(sid),
                    "deviceId": reading_item.deviceId,
                    "productionLineId": str(reading_item.productionLineId),
                    "sensorParameterId": str(reading_item.sensorParameterId),
                    "isActive": True,
                }

        for sensor_id, sensor_data in seen_sensors.items():
            try:
                await self._sync_sensor(sensor_data)
                sensors_synced += 1
            except Exception as e:
                logger.error("sensor_sync_error", sensor_id=sensor_id, error=str(e)[:200])

        if sensors_synced > 0:
            await self.db.commit()
            logger.info("sensors_synced", count=sensors_synced)

        # Phase 3: Create SensorReading records
        for reading_item in readings_response.readings:
            sensor_id = reading_item.sensorId

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

            batch.append(dict(
                id=reading_item.id,
                sensor_id=sensor_id,
                value=Decimal(str(reading_item.value)) if reading_item.value is not None else None,
                quality=reading_item.quality.lower() if reading_item.quality else None,
                recorded_at=recorded_at,
                snapshot_date=snapshot_date,
            ))

            if len(batch) >= batch_size:
                try:
                    stmt = insert(SensorReading).values(batch)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['id'],
                        set_={k: stmt.excluded[k] for k in ['value', 'quality', 'recorded_at', 'snapshot_date']},
                    )
                    await self.db.execute(stmt)
                    await self.db.commit()
                    records_processed += len(batch)
                    logger.info("sensors_sync_batch", records_processed=records_processed)
                except Exception as e:
                    await self.db.rollback()
                    logger.error("sensors_sync_batch_error", error=str(e)[:200])
                batch = []

        if batch:
            try:
                stmt = insert(SensorReading).values(batch)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['id'],
                    set_={k: stmt.excluded[k] for k in ['value', 'quality', 'recorded_at', 'snapshot_date']},
                )
                await self.db.execute(stmt)
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

    async def upsert_sensor_reading_from_event(self, payload: "SensorReadingRecordedPayload", event_id: Optional[str] = None) -> None:
        """Upsert sensor reading from event. Idempotent by reading id."""
        from app.messaging.schemas import SensorReadingRecordedPayload
        from decimal import Decimal as D

        # Check if reading already exists
        existing = await self.db.execute(
            select(SensorReading).where(SensorReading.id == payload.id)
        )
        if existing.scalar_one_or_none():
            return

        # Ensure sensor exists (upsert by sensor_id)
        sensor_result = await self.db.execute(
            select(Sensor).where(Sensor.id == payload.sensor_id)
        )
        if not sensor_result.scalar_one_or_none():
            # Find or create sensor parameter
            param_result = await self.db.execute(
                select(SensorParameter).where(SensorParameter.name == payload.parameter_name)
            )
            param = param_result.scalars().first()
            if not param:
                param = SensorParameter(
                    name=payload.parameter_name,
                    code=payload.parameter_name.lower().replace(" ", "_"),
                    unit=payload.unit,
                )
                self.db.add(param)
                await self.db.flush()

            sensor = Sensor(
                id=payload.sensor_id,
                device_id=payload.device_id,
                production_line_id=payload.production_line_id,
                sensor_parameter_id=param.id,
                parameter_name=payload.parameter_name,
                parameter_unit=payload.unit,
                is_active=True,
            )
            self.db.add(sensor)
            await self.db.flush()

        reading = SensorReading(
            id=payload.id,
            sensor_id=payload.sensor_id,
            value=D(str(payload.value)),
            quality=payload.quality.lower(),
            recorded_at=payload.recorded_at,
            snapshot_date=payload.recorded_at,
        )
        self.db.add(reading)
        await self.db.commit()

    async def upsert_anomaly_from_event(self, payload: "SensorAnomalyPayload", event_id: Optional[str] = None) -> None:
        """Upsert sensor anomaly from event. Idempotent by event_id."""
        from app.messaging.schemas import SensorAnomalyPayload
        from app.models.sensor_anomaly import SensorAnomaly
        from decimal import Decimal as D

        effective_event_id = event_id or str(payload.reading_id)

        existing = await self.db.execute(
            select(SensorAnomaly).where(SensorAnomaly.event_id == effective_event_id)
        )
        if existing.scalar_one_or_none():
            return

        anomaly = SensorAnomaly(
            reading_id=payload.reading_id,
            device_id=payload.device_id,
            production_line_id=payload.production_line_id,
            parameter_name=payload.parameter_name,
            value=D(str(payload.value)),
            unit=payload.unit,
            quality=payload.quality.lower(),
            anomaly_type=payload.anomaly_type,
            severity=payload.severity,
            reason=payload.reason,
            lower_limit=D(str(payload.lower_limit)) if payload.lower_limit is not None else None,
            upper_limit=D(str(payload.upper_limit)) if payload.upper_limit is not None else None,
            detected_at=payload.detected_at,
            event_id=effective_event_id,
        )
        self.db.add(anomaly)
        await self.db.commit()
