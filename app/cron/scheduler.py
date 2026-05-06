"""
APScheduler configuration and management.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog

from app.config import settings
from app.cron.jobs import (
    sync_kpi_task, sync_sales_task, sync_orders_task, sync_quality_task,
    sync_products_task, sync_output_task, sync_sensors_task, sync_inventory_task,
)

logger = structlog.get_logger()

# Global scheduler instance
scheduler: AsyncIOScheduler = None


def start_scheduler():
    """Start the APScheduler with configured jobs."""
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.warning("scheduler_already_running")
        return
    
    scheduler = AsyncIOScheduler()
    
    # Add jobs - run every hour at minute 0
    scheduler.add_job(
        sync_kpi_task,
        trigger=CronTrigger(minute=0),  # Every hour
        id="sync_kpi",
        name="Sync KPI from Gateway",
        replace_existing=True
    )
    
    scheduler.add_job(
        sync_sales_task,
        trigger=CronTrigger(minute=5),  # Every hour at minute 5
        id="sync_sales",
        name="Sync Sales from Gateway",
        replace_existing=True
    )
    
    scheduler.add_job(
        sync_orders_task,
        trigger=CronTrigger(minute=10),  # Every hour at minute 10
        id="sync_orders",
        name="Sync Orders from Gateway",
        replace_existing=True
    )
    
    scheduler.add_job(
        sync_quality_task,
        trigger=CronTrigger(minute=15),  # Every hour at minute 15
        id="sync_quality",
        name="Sync Quality from Gateway",
        replace_existing=True
    )
    
    scheduler.add_job(
        sync_products_task,
        trigger=CronTrigger(minute=20),  # Every hour at minute 20
        id="sync_products",
        name="Sync Products from Gateway",
        replace_existing=True
    )
    
    scheduler.add_job(
        sync_output_task,
        trigger=CronTrigger(minute=25),  # Every hour at minute 25
        id="sync_output",
        name="Sync Output from Gateway",
        replace_existing=True
    )
    
    scheduler.add_job(
        sync_sensors_task,
        trigger=CronTrigger(minute=30),  # Every hour at minute 30
        id="sync_sensors",
        name="Sync Sensors from Gateway",
        replace_existing=True
    )
    
    scheduler.add_job(
        sync_inventory_task,
        trigger=CronTrigger(minute=35),  # Every hour at minute 35
        id="sync_inventory",
        name="Sync Inventory from Gateway",
        replace_existing=True
    )
    
    # Cleanup job - run daily at 3:00 AM
    scheduler.add_job(
        cleanup_old_data_task,
        trigger=CronTrigger(hour=3, minute=0),
        id="cleanup_old_data",
        name="Cleanup data older than retention period",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("scheduler_started", jobs=[job.id for job in scheduler.get_jobs()])


def stop_scheduler():
    """Stop the scheduler."""
    global scheduler
    
    if scheduler is not None and scheduler.running:
        scheduler.shutdown()
        logger.info("scheduler_stopped")


async def cleanup_old_data_task():
    """Cleanup old data based on retention settings."""
    from datetime import datetime, timedelta
    from sqlalchemy import delete
    from app.database import AsyncSessionLocal
    from app.models import (
        OrderSnapshot, QualityResult, SyncLog, SyncError,
        ProductionOutput, SensorReading, InventorySnapshot, SaleRecord,
    )
    
    logger.info("cleanup_old_data_started", retention_days=settings.retention_days)
    
    cutoff_date = datetime.utcnow() - timedelta(days=settings.retention_days)
    
    async with AsyncSessionLocal() as db:
        try:
            # Delete old order snapshots
            result = await db.execute(
                delete(OrderSnapshot).where(OrderSnapshot.created_at < cutoff_date)
            )
            orders_deleted = result.rowcount
            
            # Delete old quality results
            result = await db.execute(
                delete(QualityResult).where(QualityResult.created_at < cutoff_date)
            )
            quality_deleted = result.rowcount
            
            # Delete old production output
            result = await db.execute(
                delete(ProductionOutput).where(ProductionOutput.created_at < cutoff_date)
            )
            output_deleted = result.rowcount
            
            # Delete old sensor readings
            result = await db.execute(
                delete(SensorReading).where(SensorReading.created_at < cutoff_date)
            )
            sensors_deleted = result.rowcount
            
            # Delete old inventory snapshots
            result = await db.execute(
                delete(InventorySnapshot).where(InventorySnapshot.created_at < cutoff_date)
            )
            inventory_deleted = result.rowcount
            
            # Delete old sale records
            result = await db.execute(
                delete(SaleRecord).where(SaleRecord.created_at < cutoff_date)
            )
            sales_raw_deleted = result.rowcount
            
            # Delete old sync logs (and their errors via cascade)
            result = await db.execute(
                delete(SyncLog).where(SyncLog.created_at < cutoff_date)
            )
            logs_deleted = result.rowcount
            
            await db.commit()
            
            logger.info(
                "cleanup_old_data_completed",
                orders_deleted=orders_deleted,
                quality_deleted=quality_deleted,
                output_deleted=output_deleted,
                sensors_deleted=sensors_deleted,
                inventory_deleted=inventory_deleted,
                sales_raw_deleted=sales_raw_deleted,
                logs_deleted=logs_deleted
            )
        except Exception as e:
            await db.rollback()
            logger.error("cleanup_old_data_failed", error=str(e))
            raise
