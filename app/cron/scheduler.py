"""
Async scheduler for data synchronization with lifecycle logging.
"""
import asyncio
import structlog
from datetime import datetime, timedelta

from app.config import settings
from app.cron.jobs import (
    sync_kpi_task, sync_kpi_per_line_task, sync_sales_task, sync_orders_task, sync_quality_task,
    sync_products_task, sync_output_task, sync_sensors_task, sync_inventory_task,
    sync_personnel_task, sync_references_task, sync_batch_inputs_task, sync_downtime_events_task,
    sync_promo_campaigns_task,
)

logger = structlog.get_logger()

# Global scheduler state
scheduler_task: asyncio.Task = None
running = False


async def run_scheduled_jobs():
    """Run scheduled jobs in an infinite loop."""
    global running
    running = True

    while running:
        try:
            # Get current wall clock time
            now = datetime.utcnow()
            current_minute = now.minute

            logger.info("scheduler_check", current_minute=current_minute, current_time=now.isoformat())

            jobs_to_run = []
            if current_minute == 0:
                jobs_to_run.append(("kpi", sync_kpi_task))
            elif current_minute == 2:
                jobs_to_run.append(("kpi_per_line", sync_kpi_per_line_task))
            elif current_minute == 5:
                jobs_to_run.append(("sales", sync_sales_task))
            elif current_minute == 10:
                jobs_to_run.append(("orders", sync_orders_task))
            elif current_minute == 15:
                jobs_to_run.append(("quality", sync_quality_task))
            elif current_minute == 20:
                jobs_to_run.append(("products", sync_products_task))
            elif current_minute == 25:
                jobs_to_run.append(("output", sync_output_task))
            elif current_minute == 30:
                jobs_to_run.append(("sensors", sync_sensors_task))
            elif current_minute == 35:
                jobs_to_run.append(("inventory", sync_inventory_task))
            elif current_minute == 40:
                jobs_to_run.append(("personnel", sync_personnel_task))
            elif current_minute == 45:
                jobs_to_run.append(("references", sync_references_task))
            elif current_minute == 48:
                jobs_to_run.append(("batch_inputs", sync_batch_inputs_task))
            elif current_minute == 52:
                jobs_to_run.append(("downtime_events", sync_downtime_events_task))
            elif current_minute == 55:
                jobs_to_run.append(("promo_campaigns", sync_promo_campaigns_task))

            # Run jobs
            for job_name, job_func in jobs_to_run:
                logger.info("scheduler_job_start", job=job_name)
                try:
                    await job_func()
                    logger.info("scheduler_job_completed", job=job_name)
                except Exception as e:
                    logger.error("scheduler_job_failed", job=job_name, error=str(e))
            
            # Sleep until next minute
            logger.info("scheduler_sleep", seconds=60)
            await asyncio.sleep(60)
            
        except asyncio.CancelledError:
            logger.info("scheduler_cancelled")
            break
        except Exception as e:
            logger.error("scheduler_error", error=str(e))
            await asyncio.sleep(60)


def start_scheduler():
    """Start the async scheduler."""
    global scheduler_task, running

    if running:
        logger.warning(
            "scheduler_lifecycle",
            phase="startup",
            action="start",
            state="already_running",
        )
        return

    scheduler_task = asyncio.create_task(run_scheduled_jobs())
    
    logger.info(
        "scheduler_lifecycle",
        phase="startup",
        action="start",
        state="running",
    )


def stop_scheduler():
    """Stop the scheduler."""
    global scheduler_task, running

    if scheduler_task and not scheduler_task.done():
        scheduler_task.cancel()
        try:
            asyncio.run_coroutine_threadsafe(scheduler_task, asyncio.get_event_loop())
        except:
            pass
    
    running = False
    
    logger.info(
        "scheduler_lifecycle",
        phase="shutdown",
        action="stop",
        state="stopped",
    )
