"""
Cron job definitions for data synchronization.
"""
from datetime import date, timedelta
import structlog

from app.database import AsyncSessionLocal
from app.models import SyncLog, SyncStatus
from app.services import GatewayClient, KPIService, SalesService, OrderService, QualityService, ProductService, OutputService, SensorService, InventoryService
from app.config import settings
from sqlalchemy import select, func

logger = structlog.get_logger()


async def _has_any_records(model_class) -> bool:
    """Check if table has any records (to determine initial vs incremental sync)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.count()).select_from(model_class))
        count = result.scalar()
        return count > 0


async def create_sync_log(db: AsyncSessionLocal, task_name: str) -> SyncLog:
    """Create a new sync log entry."""
    from datetime import datetime
    
    log = SyncLog(
        task_name=task_name,
        status=SyncStatus.RUNNING.value,
        started_at=datetime.utcnow(),
        records_processed=0,
        records_inserted=0,
        records_updated=0
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def complete_sync_log(
    db: AsyncSessionLocal,
    log: SyncLog,
    status: SyncStatus,
    records_processed: int = 0,
    error_message: str = None
):
    """Complete sync log entry."""
    from datetime import datetime
    
    log.status = status.value
    log.completed_at = datetime.utcnow()
    log.records_processed = records_processed
    log.error_message = error_message
    await db.commit()


async def sync_kpi_task():
    """Sync KPI data from Gateway."""
    logger.info("sync_kpi_task_started")
    
    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "kpi")
        gateway = GatewayClient()
        service = KPIService(db, gateway)
        
        try:
            from app.models import AggregatedKPI
            
            # Initial sync: fetch all data; Incremental: 1 month ending at current week
            if await _has_any_records(AggregatedKPI):
                today = date.today()
                # Monday = 0 in weekday(), Sunday = 6
                monday = today - timedelta(days=today.weekday())
                sunday = monday + timedelta(days=6)
                # Period: 1 month before current week end → current week end
                from_date = sunday - timedelta(days=30)
                to_date = sunday
                logger.info("kpi_incremental_sync_month_to_week", from_date=from_date.isoformat(), to_date=to_date.isoformat())
                records = await service.sync_from_gateway(from_date, to_date)
            else:
                logger.info("kpi_initial_sync_no_date_filter")
                records = await service.sync_from_gateway(None, None)
            
            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
            logger.info("sync_kpi_task_completed", records_processed=records)
        except Exception as e:
            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=str(e))
            logger.error("sync_kpi_task_failed", error=str(e))
            raise
        finally:
            await gateway.close()


async def sync_sales_task():
    """Sync sales data from Gateway."""
    logger.info("sync_sales_task_started")
    
    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "sales")
        gateway = GatewayClient()
        service = SalesService(db, gateway)
        
        try:
            from app.models import AggregatedSales
            
            if await _has_any_records(AggregatedSales):
                from_date = date.today() - timedelta(days=1)
                to_date = date.today()
                records = await service.sync_from_gateway(from_date, to_date)
            else:
                logger.info("sales_initial_sync_no_date_filter")
                records = await service.sync_from_gateway(None, None)
            
            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
            logger.info("sync_sales_task_completed", records_processed=records)
        except Exception as e:
            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=str(e))
            logger.error("sync_sales_task_failed", error=str(e))
            raise
        finally:
            await gateway.close()


async def sync_orders_task():
    """Sync orders data from Gateway."""
    logger.info("sync_orders_task_started")
    
    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "orders")
        gateway = GatewayClient()
        service = OrderService(db, gateway)
        
        try:
            from app.models import OrderSnapshot
            
            if await _has_any_records(OrderSnapshot):
                from_date = date.today() - timedelta(days=1)
                to_date = date.today()
                records = await service.sync_from_gateway(from_date, to_date)
            else:
                logger.info("orders_initial_sync_no_date_filter")
                records = await service.sync_from_gateway(None, None)
            
            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
            logger.info("sync_orders_task_completed", records_processed=records)
        except Exception as e:
            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=str(e))
            logger.error("sync_orders_task_failed", error=str(e))
            raise
        finally:
            await gateway.close()


async def sync_quality_task():
    """Sync quality data from Gateway."""
    logger.info("sync_quality_task_started")
    
    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "quality")
        gateway = GatewayClient()
        service = QualityService(db, gateway)
        
        try:
            from app.models import QualityResult
            
            if await _has_any_records(QualityResult):
                from_date = date.today() - timedelta(days=1)
                to_date = date.today()
                records = await service.sync_from_gateway(from_date, to_date)
            else:
                logger.info("quality_initial_sync_no_date_filter")
                records = await service.sync_from_gateway(None, None)
            
            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
            logger.info("sync_quality_task_completed", records_processed=records)
        except Exception as e:
            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=str(e))
            logger.error("sync_quality_task_failed", error=str(e))
            raise
        finally:
            await gateway.close()


async def sync_products_task():
    """Sync products from Gateway (full upsert each time)."""
    logger.info("sync_products_task_started")
    
    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "products")
        gateway = GatewayClient()
        service = ProductService(db, gateway)
        
        try:
            records = await service.sync_from_gateway()
            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
            logger.info("sync_products_task_completed", records_processed=records)
        except Exception as e:
            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=str(e))
            logger.error("sync_products_task_failed", error=str(e))
            raise
        finally:
            await gateway.close()


async def sync_output_task():
    """Sync output data from Gateway."""
    logger.info("sync_output_task_started")
    
    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "output")
        gateway = GatewayClient()
        service = OutputService(db, gateway)
        
        try:
            from app.models import ProductionOutput
            
            if await _has_any_records(ProductionOutput):
                from_date = date.today() - timedelta(days=1)
                to_date = date.today()
                records = await service.sync_from_gateway(from_date, to_date)
            else:
                logger.info("output_initial_sync_no_date_filter")
                records = await service.sync_from_gateway(None, None)
            
            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
            logger.info("sync_output_task_completed", records_processed=records)
        except Exception as e:
            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=str(e))
            logger.error("sync_output_task_failed", error=str(e))
            raise
        finally:
            await gateway.close()


async def sync_sensors_task():
    """Sync sensor readings from Gateway."""
    logger.info("sync_sensors_task_started")
    
    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "sensors")
        gateway = GatewayClient()
        service = SensorService(db, gateway)
        
        try:
            from app.models import SensorReading
            
            if await _has_any_records(SensorReading):
                from_date = date.today() - timedelta(days=1)
                to_date = date.today()
                records = await service.sync_from_gateway(from_date, to_date)
            else:
                logger.info("sensors_initial_sync_no_date_filter")
                records = await service.sync_from_gateway(None, None)
            
            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
            logger.info("sync_sensors_task_completed", records_processed=records)
        except Exception as e:
            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=str(e))
            logger.error("sync_sensors_task_failed", error=str(e))
            raise
        finally:
            await gateway.close()


async def sync_inventory_task():
    """Sync inventory from Gateway (snapshot current state)."""
    logger.info("sync_inventory_task_started")
    
    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "inventory")
        gateway = GatewayClient()
        service = InventoryService(db, gateway)
        
        try:
            records = await service.sync_from_gateway()
            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
            logger.info("sync_inventory_task_completed", records_processed=records)
        except Exception as e:
            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=str(e))
            logger.error("sync_inventory_task_failed", error=str(e))
            raise
        finally:
            await gateway.close()
