"""
Sensor business logic service.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict

from sqlalchemy import select, func, desc, and_, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SensorReading
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
import structlog

logger = structlog.get_logger()


class SensorService:
    """Service for Sensor readings business logic."""
    
    def __init__(self, db: AsyncSession, gateway: GatewayClient):
        self.db = db
        self.gateway = gateway
    
    async def get_sensor_history(
        self,
        production_line: Optional[str] = None,
        parameter_name: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 500
    ) -> Dict:
        """Get sensor readings history for trends."""
        query = select(SensorReading).order_by(desc(SensorReading.recorded_at))
        
        if production_line:
            query = query.where(SensorReading.production_line == production_line)
        if parameter_name:
            query = query.where(SensorReading.parameter_name == parameter_name)
        if from_date:
            query = query.where(SensorReading.recorded_at >= from_date)
        if to_date:
            query = query.where(SensorReading.recorded_at <= to_date)
        
        query = query.limit(limit)
        result = await self.db.execute(query)
        readings = result.scalars().all()
        
        items = [
            {
                "device_id": r.device_id,
                "production_line": r.production_line,
                "parameter_name": r.parameter_name,
                "value": float(r.value) if r.value else None,
                "unit": r.unit,
                "quality": r.quality,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in readings
        ]
        
        return {"items": items, "count": len(items)}
    
    async def get_sensor_alerts(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100
    ) -> Dict:
        """Get sensor readings with quality issues (alerts)."""
        query = select(SensorReading).where(
            SensorReading.quality.in_(["BAD", "DEGRADED"])
        ).order_by(desc(SensorReading.recorded_at))
        
        if from_date:
            query = query.where(SensorReading.recorded_at >= from_date)
        if to_date:
            query = query.where(SensorReading.recorded_at <= to_date)
        
        query = query.limit(limit)
        result = await self.db.execute(query)
        readings = result.scalars().all()
        
        items = [
            {
                "device_id": r.device_id,
                "production_line": r.production_line,
                "parameter_name": r.parameter_name,
                "value": float(r.value) if r.value else None,
                "unit": r.unit,
                "quality": r.quality,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in readings
        ]
        
        return {"items": items, "count": len(items)}
    
    async def get_sensor_stats(
        self,
        production_line: Optional[str] = None
    ) -> Dict:
        """Get aggregated statistics per parameter per line."""
        query = select(
            SensorReading.production_line,
            SensorReading.parameter_name,
            SensorReading.unit,
            func.avg(SensorReading.value).label("avg_value"),
            func.min(SensorReading.value).label("min_value"),
            func.max(SensorReading.value).label("max_value"),
            func.count(SensorReading.id).label("reading_count"),
            func.sum(func.cast(SensorReading.quality.in_(["BAD", "DEGRADED"]), type_=Integer)).label("alert_count")  # noqa
        ).group_by(
            SensorReading.production_line,
            SensorReading.parameter_name,
            SensorReading.unit
        )
        
        if production_line:
            query = query.where(SensorReading.production_line == production_line)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        items = [
            {
                "production_line": row.production_line,
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
    
    @track_feature_path(feature_name="sensors.sync_from_gateway", log_result=True)
    async def sync_from_gateway(
        self,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> int:
        """Sync sensor readings from Gateway."""
        logger.info("syncing_sensors_from_gateway", from_date=from_date, to_date=to_date)
        
        gateway_data = await self.gateway.get_sensors(from_date=from_date, to_date=to_date)
        readings = gateway_data.get("readings", [])
        logger.info("sensors_fetched_from_gateway", total_readings=len(readings))
        
        records_processed = 0
        batch_size = 50
        batch = []
        snapshot_date = datetime.utcnow()
        
        for reading_data in readings:
            # Parse recorded_at
            recorded_at_raw = reading_data.get("recordedAt", datetime.utcnow())
            if isinstance(recorded_at_raw, str):
                try:
                    recorded_at = datetime.fromisoformat(recorded_at_raw.replace("Z", "+00:00"))
                except ValueError:
                    recorded_at = datetime.utcnow()
            elif isinstance(recorded_at_raw, datetime):
                recorded_at = recorded_at_raw
            else:
                recorded_at = datetime.utcnow()
            
            reading = SensorReading(
                device_id=reading_data.get("deviceId", ""),
                production_line=reading_data.get("productionLine", ""),
                parameter_name=reading_data.get("parameterName", ""),
                value=Decimal(str(reading_data.get("value", 0))) if reading_data.get("value") is not None else None,
                unit=reading_data.get("unit", ""),
                quality=reading_data.get("quality", "").lower() if reading_data.get("quality") else None,
                recorded_at=recorded_at,
                snapshot_date=snapshot_date
            )
            batch.append(reading)
            
            if len(batch) >= batch_size:
                try:
                    self.db.add_all(batch)
                    await self.db.commit()
                    records_processed += len(batch)
                    logger.info("sensors_sync_batch", records_processed=records_processed)
                except Exception as e:
                    await self.db.rollback()
                    logger.error("sensors_sync_batch_error", error=str(e)[:200])
                batch = []
        
        if batch:
            try:
                self.db.add_all(batch)
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
        logger.info("sensors_sync_completed", records_processed=records_processed)
        return records_processed
