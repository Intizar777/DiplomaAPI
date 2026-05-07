"""
APScheduler configuration and management with lifecycle logging.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog

from app.config import settings
from app.cron.jobs import (
    sync_kpi_task, sync_sales_task, sync_orders_task, sync_quality_task,
    sync_products_task, sync_output_task, sync_sensors_task, sync_inventory_task,
    sync_personnel_task, cleanup_old_data_task,
)

logger = structlog.get_logger()

# Global scheduler instance
scheduler: AsyncIOScheduler = None


def start_scheduler():
    """Start the APScheduler with configured jobs."""
    global scheduler

    if scheduler is not None and scheduler.running:
        logger.warning(
            "scheduler_lifecycle",
            phase="startup",
            action="start",
            state="already_running",
        )
        return

    scheduler = AsyncIOScheduler()

    # Add jobs - run every hour at minute 0
    jobs_config = [
        (sync_kpi_task, CronTrigger(minute=0), "sync_kpi", "Sync KPI from Gateway"),
        (sync_sales_task, CronTrigger(minute=5), "sync_sales", "Sync Sales from Gateway"),
        (sync_orders_task, CronTrigger(minute=10), "sync_orders", "Sync Orders from Gateway"),
        (sync_quality_task, CronTrigger(minute=15), "sync_quality", "Sync Quality from Gateway"),
        (sync_products_task, CronTrigger(minute=20), "sync_products", "Sync Products from Gateway"),
        (sync_output_task, CronTrigger(minute=25), "sync_output", "Sync Output from Gateway"),
        (sync_sensors_task, CronTrigger(minute=30), "sync_sensors", "Sync Sensors from Gateway"),
        (sync_inventory_task, CronTrigger(minute=35), "sync_inventory", "Sync Inventory from Gateway"),
        (sync_personnel_task, CronTrigger(minute=40), "sync_personnel", "Sync Personnel from Gateway"),
    ]

    for func, trigger, job_id, name in jobs_config:
        scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name,
            replace_existing=True,
        )

    # Cleanup job - run daily at 3:00 AM
    scheduler.add_job(
        cleanup_old_data_task,
        trigger=CronTrigger(hour=3, minute=0),
        id="cleanup_old_data",
        name="Cleanup data older than retention period",
        replace_existing=True,
    )

    scheduler.start()
    registered_jobs = [job.id for job in scheduler.get_jobs()]
    logger.info(
        "scheduler_lifecycle",
        phase="startup",
        action="start",
        state="running",
        jobs=registered_jobs,
        job_count=len(registered_jobs),
    )


def stop_scheduler():
    """Stop the scheduler."""
    global scheduler

    if scheduler is not None and scheduler.running:
        scheduler.shutdown()
        logger.info(
            "scheduler_lifecycle",
            phase="shutdown",
            action="stop",
            state="stopped",
        )
    else:
        logger.info(
            "scheduler_lifecycle",
            phase="shutdown",
            action="stop",
            state="not_running",
        )
