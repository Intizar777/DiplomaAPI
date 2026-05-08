"""
Sync status API routes.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SyncLog, SyncStatus
from app.schemas import SyncStatusResponse, SyncTriggerResponse
from app.config import settings
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/sync", tags=["Sync"])

# Track running tasks
_running_tasks: set = set()


async def _run_sync_task(task_name: str):
    """Run a sync task with proper sync log creation."""
    from app.cron.jobs import (
        sync_kpi_task, sync_sales_task, sync_orders_task, sync_quality_task,
        sync_products_task, sync_output_task, sync_sensors_task, sync_inventory_task,
        sync_personnel_task,
    )

    task_map = {
        "kpi": sync_kpi_task,
        "sales": sync_sales_task,
        "orders": sync_orders_task,
        "quality": sync_quality_task,
        "products": sync_products_task,
        "output": sync_output_task,
        "sensors": sync_sensors_task,
        "inventory": sync_inventory_task,
        "personnel": sync_personnel_task,
    }

    if task_name not in task_map:
        logger.error("unknown_sync_task", task_name=task_name)
        return

    # Call the cron job function directly - it handles its own sync log creation
    await task_map[task_name]()


async def _run_cleanup_task():
    """Run data cleanup task."""
    from app.cron.jobs import cleanup_old_data_task
    await cleanup_old_data_task()


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of all synchronization tasks.
    
    Returns current status, last run time, and statistics for each task.
    """
    tasks = ["kpi", "sales", "orders", "quality", "products", "output", "sensors", "inventory", "personnel"]
    task_statuses = []
    
    for task_name in tasks:
        query = select(SyncLog).where(
            SyncLog.task_name == task_name
        ).order_by(desc(SyncLog.started_at)).limit(1)
        
        result = await db.execute(query)
        latest = result.scalar_one_or_none()
        
        success_query = select(SyncLog).where(
            SyncLog.task_name == task_name,
            SyncLog.status == SyncStatus.COMPLETED.value
        ).order_by(desc(SyncLog.completed_at)).limit(1)
        
        success_result = await db.execute(success_query)
        last_success = success_result.scalar_one_or_none()
        
        # Check if currently running
        is_running = task_name in _running_tasks
        
        task_statuses.append({
            "task_name": task_name,
            "status": "running" if is_running else (latest.status if latest else "unknown"),
            "last_run": latest.started_at if latest else None,
            "last_success": last_success.completed_at if last_success else None,
            "records_processed": latest.records_processed if latest else 0,
            "records_inserted": latest.records_inserted if latest else 0,
            "records_updated": latest.records_updated if latest else 0,
            "error_message": latest.error_message if latest else None
        })
    
    all_completed = all(
        t["status"] == SyncStatus.COMPLETED.value or t["status"] == "unknown"
        for t in task_statuses
    )
    any_failed = any(t["status"] == SyncStatus.FAILED.value for t in task_statuses)
    any_running = any(t["status"] == "running" for t in task_statuses)
    
    if any_running:
        overall = "syncing"
    elif all_completed and not any_failed:
        overall = "healthy"
    elif any_failed:
        overall = "failed"
    else:
        overall = "degraded"
    
    last_sync = max(
        (t["last_run"] for t in task_statuses if t["last_run"]),
        default=None
    )
    
    return SyncStatusResponse(
        tasks=task_statuses,
        overall_status=overall,
        last_sync=last_sync
    )


@router.post("/trigger", response_model=SyncTriggerResponse)
async def trigger_sync_all(
    background_tasks: BackgroundTasks
):
    """
    Manually trigger all synchronization tasks.
    
    Tasks run in background — API returns immediately.
    Check /sync/status for progress.
    """
    tasks = ["kpi", "sales", "orders", "quality", "products", "output", "sensors", "inventory", "personnel"]
    triggered = []
    skipped = []
    
    for task_name in tasks:
        if task_name in _running_tasks:
            skipped.append(task_name)
        else:
            background_tasks.add_task(_run_sync_task, task_name)
            triggered.append(task_name)
    
    logger.info("sync_all_triggered", triggered=triggered, skipped=skipped)
    
    return SyncTriggerResponse(
        message=f"Sync tasks triggered: {triggered}" + (f", already running: {skipped}" if skipped else ""),
        triggered_tasks=triggered
    )


@router.post("/trigger/{task_name}", response_model=SyncTriggerResponse)
async def trigger_sync_task(
    task_name: str
):
    """
    Manually trigger a specific synchronization task.

    Available tasks: kpi, sales, orders, quality, products, output, sensors, inventory, personnel
    Tasks run synchronously for testing - API waits for completion.
    """
    valid_tasks = ["kpi", "sales", "orders", "quality", "products", "output", "sensors", "inventory", "personnel"]

    if task_name not in valid_tasks:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task '{task_name}'. Valid tasks: {valid_tasks}"
        )

    if task_name in _running_tasks:
        return SyncTriggerResponse(
            message=f"Task '{task_name}' is already running",
            triggered_tasks=[]
        )

    _running_tasks.add(task_name)

    try:
        logger.info("manual_sync_task_start", task_name=task_name)
        await _run_sync_task(task_name)
        logger.info("manual_sync_task_completed", task_name=task_name)
    except Exception as e:
        logger.error("manual_sync_task_failed", task_name=task_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
    finally:
        _running_tasks.discard(task_name)

    return SyncTriggerResponse(
        message=f"Task '{task_name}' completed",
        triggered_tasks=[task_name]
    )


@router.post("/cleanup", response_model=dict)
async def trigger_cleanup():
    """
    Manually trigger data cleanup task.

    Removes all records older than retention_days (from config).
    Deletes from: orders, quality, output, sensors, inventory, sales, and sync logs.
    Task runs synchronously - API waits for completion.
    """
    cleanup_task_name = "cleanup"

    if cleanup_task_name in _running_tasks:
        return {
            "message": "Cleanup task is already running",
            "status": "running"
        }

    _running_tasks.add(cleanup_task_name)

    try:
        logger.info("manual_cleanup_start")
        await _run_cleanup_task()
        logger.info("manual_cleanup_completed")
        return {
            "message": "Data cleanup completed successfully",
            "status": "completed"
        }
    except Exception as e:
        logger.error("manual_cleanup_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
    finally:
        _running_tasks.discard(cleanup_task_name)
