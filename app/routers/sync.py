"""
Sync status API routes.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SyncLog, SyncStatus
from app.schemas import SyncStatusResponse, SyncTriggerResponse
from app.config import settings
from app.services import GatewayClient
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/sync", tags=["Sync"])

# Track running tasks as (task_name -> asyncio.Task)
_running_tasks: Dict[str, asyncio.Task] = {}


async def _run_sync_task(task_name: str):
    """Run a sync task with proper sync log creation."""
    from app.cron.jobs import (
        sync_kpi_task, sync_kpi_per_line_task, sync_sales_task, sync_orders_task, sync_quality_task,
        sync_products_task, sync_output_task, sync_sensors_task, sync_inventory_task,
        sync_references_task,
    )

    task_map = {
        "kpi": sync_kpi_task,
        "kpi_per_line": sync_kpi_per_line_task,
        "sales": sync_sales_task,
        "orders": sync_orders_task,
        "quality": sync_quality_task,
        "products": sync_products_task,
        "output": sync_output_task,
        "sensors": sync_sensors_task,
        "inventory": sync_inventory_task,
        "references": sync_references_task,
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


async def _run_initial_sync():
    """
    Run initial bulk synchronization in background.
    Syncs ALL tables in dependency order to avoid FK violations.
    """
    from app.database import AsyncSessionLocal
    from app.models import (
        SyncLog, SyncStatus, Customer, Warehouse
    )
    from app.services import (
        ProductService, SensorService, SalesService,
        InventoryService, OutputService, QualityService, OrderService,
        KPIService
    )

    async with AsyncSessionLocal() as db:
        log = SyncLog(
            task_name="initial_sync",
            status=SyncStatus.RUNNING.value,
            started_at=datetime.utcnow(),
            records_processed=0,
            records_inserted=0,
            records_updated=0
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)

        summary = {
            "level_0": {},
            "level_1": {},
            "level_2": {},
            "level_3": {},
            "total_records": 0,
            "errors": []
        }

        gateway = GatewayClient()
        total_records = 0

        try:
            logger.info("initial_sync_started_background", task_id="initial_sync")

            # Level 0: Reference tables (no FK dependencies)
            try:
                logger.info("initial_sync_phase_0", phase="reference_tables")

                # UnitOfMeasure via Product service
                product_service = ProductService(db, gateway)
                count = 0
                try:
                    gateway_data = await gateway.get_units_of_measure()
                    units = gateway_data.unitsOfMeasure
                    logger.info("initial_sync_units_fetched", count=len(units))
                    for unit_data in units:
                        await product_service._sync_unit_of_measure(unit_data)
                        count += 1
                    await db.commit()
                except Exception as e:
                    logger.warning("initial_sync_units_error", error=str(e)[:100])
                summary["level_0"]["units_of_measure"] = count
                total_records += count

                # SensorParameter via Sensor service (endpoint may not exist)
                count = 0
                try:
                    sensor_service = SensorService(db, gateway)
                    gateway_data = await gateway.get_sensor_parameters()
                    params = gateway_data.get("parameters", [])
                    logger.info("initial_sync_sensor_params_fetched", count=len(params))
                    for param_data in params:
                        await sensor_service._sync_sensor_parameter(param_data)
                        count += 1
                    await db.commit()
                except Exception as e:
                    logger.warning("initial_sync_sensor_parameters_error", error=str(e)[:100])
                summary["level_0"]["sensor_parameters"] = count
                total_records += count

                # Customer (needed by SaleRecord)
                count = 0
                try:
                    gateway_data = await gateway.get_customers()
                    customers = gateway_data.customers
                    logger.info("initial_sync_customers_fetched", count=len(customers))
                    for customer_data in customers:
                        customer_id = customer_data.id
                        code = getattr(customer_data, "code", None) or str(customer_id)[:8]
                        if customer_id:
                            existing = await db.execute(
                                select(Customer).where(Customer.id == customer_id)
                            )
                            customer = existing.scalar_one_or_none()
                            if customer:
                                customer.name = customer_data.name
                                customer.region = getattr(customer_data, "region", "Unknown")
                                customer.is_active = getattr(customer_data, "isActive", True)
                            else:
                                customer = Customer(
                                    id=customer_id,
                                    code=code,
                                    name=customer_data.name,
                                    region=getattr(customer_data, "region", "Unknown"),
                                    is_active=getattr(customer_data, "isActive", True)
                                )
                                db.add(customer)
                            count += 1
                    await db.commit()
                except Exception as e:
                    logger.warning("initial_sync_customers_error", error=str(e)[:100])
                summary["level_0"]["customers"] = count
                total_records += count

                # Warehouse (needed by InventorySnapshot)
                count = 0
                try:
                    gateway_data = await gateway.get_warehouses()
                    warehouses = gateway_data.warehouses
                    logger.info("initial_sync_warehouses_fetched", count=len(warehouses))
                    for warehouse_data in warehouses:
                        warehouse_id = warehouse_data.id
                        code = warehouse_data.code
                        if warehouse_id:
                            existing = await db.execute(
                                select(Warehouse).where(Warehouse.id == warehouse_id)
                            )
                            warehouse = existing.scalar_one_or_none()
                            if warehouse:
                                warehouse.code = code or warehouse.code
                                warehouse.name = warehouse_data.name
                                warehouse.location = getattr(warehouse_data, "location", "Unknown")
                                warehouse.capacity = getattr(warehouse_data, "capacity", 0)
                                warehouse.is_active = getattr(warehouse_data, "isActive", True)
                            else:
                                warehouse = Warehouse(
                                    id=warehouse_id,
                                    code=code,
                                    name=warehouse_data.name,
                                    location=getattr(warehouse_data, "location", "Unknown"),
                                    capacity=getattr(warehouse_data, "capacity", 0),
                                    is_active=getattr(warehouse_data, "isActive", True)
                                )
                                db.add(warehouse)
                            count += 1
                    await db.commit()
                except Exception as e:
                    logger.warning("initial_sync_warehouses_error", error=str(e)[:100])
                summary["level_0"]["warehouses"] = count
                total_records += count

                logger.info("initial_sync_phase_0_complete",
                           units=summary["level_0"].get("units_of_measure", 0),
                           params=summary["level_0"].get("sensor_parameters", 0),
                           customers=summary["level_0"].get("customers", 0),
                           warehouses=summary["level_0"].get("warehouses", 0))

            except Exception as e:
                error_msg = f"Level 0 error: {str(e)[:200]}"
                logger.error("initial_sync_level_0_failed", error=error_msg)
                summary["errors"].append(error_msg)

            # Level 1: Tables depending on Level 0
            try:
                logger.info("initial_sync_phase_1", phase="dependent_on_level_0")

                # Product (depends on UnitOfMeasure)
                product_service = ProductService(db, gateway)
                count = await product_service.sync_from_gateway(None, None)
                summary["level_1"]["products"] = count
                total_records += count
                logger.info("initial_sync_products_synced", count=count)

                # SaleRecord (depends on Customer via direct foreign key)
                sales_service = SalesService(db, gateway)
                count = await sales_service.sync_from_gateway(None, None)
                summary["level_1"]["sale_records"] = count
                total_records += count
                logger.info("initial_sync_sale_records_synced", count=count)

                # Sensor (depends on SensorParameter)
                sensor_service = SensorService(db, gateway)
                count = await sensor_service.sync_from_gateway(None, None)
                summary["level_1"]["sensors"] = count
                total_records += count
                logger.info("initial_sync_sensors_synced", count=count)

                # InventorySnapshot (depends on Warehouse via foreign key)
                inventory_service = InventoryService(db, gateway)
                count = await inventory_service.sync_from_gateway(None, None)
                summary["level_1"]["inventory_snapshots"] = count
                total_records += count
                logger.info("initial_sync_inventory_synced", count=count)

            except Exception as e:
                error_msg = f"Level 1 error: {str(e)[:200]}"
                logger.error("initial_sync_level_1_failed", error=error_msg)
                summary["errors"].append(error_msg)

            # Level 2: Tables depending on Level 1
            try:
                logger.info("initial_sync_phase_2", phase="dependent_on_level_1")

                # QualityResult (depends on QualitySpec which depends on Product)
                quality_service = QualityService(db, gateway)
                count = await quality_service.sync_from_gateway(None, None)
                summary["level_2"]["quality_results"] = count
                total_records += count
                logger.info("initial_sync_quality_synced", count=count)

            except Exception as e:
                error_msg = f"Level 2 error: {str(e)[:200]}"
                logger.error("initial_sync_level_2_failed", error=error_msg)
                summary["errors"].append(error_msg)

            # Level 3: Data tables (no FK dependencies)
            try:
                logger.info("initial_sync_level_3", phase="data_tables")

                # OrderSnapshot
                order_service = OrderService(db, gateway)
                count = await order_service.sync_from_gateway(None, None)
                summary["level_3"]["order_snapshots"] = count
                total_records += count
                logger.info("initial_sync_order_snapshots_synced", count=count)

                # ProductionOutput
                output_service = OutputService(db, gateway)
                count = await output_service.sync_from_gateway(None, None)
                summary["level_3"]["production_output"] = count
                total_records += count
                logger.info("initial_sync_production_output_synced", count=count)

                # KPI (AggregatedKPI - independent data)
                kpi_service = KPIService(db, gateway)
                count = await kpi_service.sync_from_gateway(None, None)
                summary["level_3"]["kpi"] = count
                total_records += count
                logger.info("initial_sync_kpi_synced", count=count)

                # KPI per production line (by individual line)
                count = await kpi_service.sync_kpi_per_line(None, None)
                summary["level_3"]["kpi_per_line"] = count
                total_records += count
                logger.info("initial_sync_kpi_per_line_synced", count=count)

            except Exception as e:
                error_msg = f"Level 3 error: {str(e)[:200]}"
                logger.error("initial_sync_level_3_failed", error=error_msg)
                summary["errors"].append(error_msg)

            # Update sync log
            log.status = SyncStatus.COMPLETED.value if not summary["errors"] else SyncStatus.FAILED.value
            log.completed_at = datetime.utcnow()
            log.records_processed = total_records
            log.records_inserted = total_records
            log.error_message = "; ".join(summary["errors"]) if summary["errors"] else None
            await db.commit()

            logger.info("initial_sync_completed_background",
                       total_records=total_records,
                       has_errors=bool(summary["errors"]),
                       status=log.status)

        except Exception as e:
            logger.error("initial_sync_background_failed", error=str(e)[:200])
            log.status = SyncStatus.FAILED.value
            log.completed_at = datetime.utcnow()
            log.error_message = str(e)[:500]
            await db.commit()


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of all synchronization tasks.

    Returns current status, last run time, and statistics for each task.
    """
    tasks = ["kpi", "kpi_per_line", "sales", "orders", "quality", "products", "output", "sensors", "inventory", "references"]
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
async def trigger_sync_all():
    """
    Manually trigger all synchronization tasks in background.

    Tasks run concurrently in background — API returns immediately.
    Check /sync/status for progress.
    Stop with POST /api/v1/sync/stop or /api/v1/sync/stop/all
    """
    all_tasks = ["kpi", "kpi_per_line", "sales", "orders", "quality", "products", "output", "sensors", "inventory", "references"]
    triggered = []
    skipped = []

    for task_name in all_tasks:
        if task_name in _running_tasks:
            skipped.append(task_name)
        else:
            # Create and track asyncio task
            task = asyncio.create_task(_run_sync_task(task_name))
            _running_tasks[task_name] = task
            # Clean up when done
            task.add_done_callback(lambda t, name=task_name: _running_tasks.pop(name, None))
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

    Available tasks: kpi, kpi_per_line, sales, orders, quality, products, output, sensors, inventory, personnel, references
    Tasks run as background tasks — API returns immediately.
    """
    valid_tasks = ["kpi", "kpi_per_line", "sales", "orders", "quality", "products", "output", "sensors", "inventory", "references"]

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

    # Create and track asyncio task
    task = asyncio.create_task(_run_sync_task(task_name))
    _running_tasks[task_name] = task
    # Clean up when done
    task.add_done_callback(lambda t: _running_tasks.pop(task_name, None))

    logger.info("manual_sync_task_triggered", task_name=task_name)

    return SyncTriggerResponse(
        message=f"Task '{task_name}' triggered in background",
        triggered_tasks=[task_name]
    )


@router.post("/cleanup", response_model=dict)
async def trigger_cleanup():
    """
    Manually trigger data cleanup task.

    Removes all records older than retention_days (from config).
    Deletes from: orders, quality, output, sensors, inventory, sales, and sync logs.
    Task runs in background — API returns immediately.
    Stop with POST /api/v1/sync/stop/cleanup
    """
    cleanup_task_name = "cleanup"

    if cleanup_task_name in _running_tasks:
        return {
            "message": "Cleanup task is already running",
            "status": "running"
        }

    # Create and track asyncio task
    task = asyncio.create_task(_run_cleanup_task())
    _running_tasks[cleanup_task_name] = task
    # Clean up when done
    task.add_done_callback(lambda t: _running_tasks.pop(cleanup_task_name, None))

    logger.info("manual_cleanup_triggered")

    return {
        "message": "Cleanup task triggered in background",
        "status": "triggered"
    }


@router.post("/stop", response_model=dict)
async def stop_all_tasks():
    """
    Stop ALL running synchronization and cleanup tasks immediately.

    Cancels all background sync jobs and cleanup.
    """
    if not _running_tasks:
        return {
            "message": "No tasks running",
            "stopped": [],
            "status": "ok"
        }

    stopped = []
    for task_name, task in list(_running_tasks.items()):
        if not task.done():
            task.cancel()
            stopped.append(task_name)
            logger.info("task_cancelled", task_name=task_name)

    # Clean up cancelled tasks
    for task_name in stopped:
        _running_tasks.pop(task_name, None)

    return {
        "message": f"Stopped {len(stopped)} task(s)",
        "stopped": stopped,
        "status": "ok"
    }


@router.post("/stop/{task_name}", response_model=dict)
async def stop_task(task_name: str):
    """
    Stop a specific running task.

    Example tasks: kpi, kpi_per_line, sales, orders, quality, products, output, sensors, inventory, personnel, cleanup
    """
    if task_name not in _running_tasks:
        return {
            "message": f"Task '{task_name}' is not running",
            "stopped": [],
            "status": "not_found"
        }

    task = _running_tasks[task_name]

    if task.done():
        _running_tasks.pop(task_name, None)
        return {
            "message": f"Task '{task_name}' already completed",
            "stopped": [],
            "status": "completed"
        }

    # Cancel the task
    task.cancel()
    _running_tasks.pop(task_name, None)

    logger.info("task_cancelled", task_name=task_name)

    return {
        "message": f"Task '{task_name}' stopped",
        "stopped": [task_name],
        "status": "ok"
    }


@router.get("/running", response_model=dict)
async def get_running_tasks():
    """
    Get list of currently running tasks.
    """
    running = []
    for task_name, task in _running_tasks.items():
        running.append({
            "name": task_name,
            "done": task.done(),
            "cancelled": task.cancelled()
        })

    return {
        "running_tasks": running,
        "count": len(running)
    }


@router.post("/initial_sync", response_model=dict)
async def initial_sync():
    """
    Initial bulk synchronization endpoint (asynchronous).

    Triggers initial sync in background. Syncs all reference and data tables from Gateway
    in correct dependency order to avoid foreign key constraint violations.

    Execution order:
    1. Level 0: Reference tables (UnitOfMeasure, SensorParameter)
    2. Level 1: Tables depending on Level 0 (Product, Sensor, InventorySnapshot, SaleRecord)
    3. Level 2: Tables depending on Level 1 (QualityResult)
    4. Level 3: Data tables (OrderSnapshot, ProductionOutput)

    API returns immediately (202 Accepted). Check /sync/status for progress.
    """
    task_name = "initial_sync"

    if task_name in _running_tasks:
        return {
            "status": "already_running",
            "message": "Initial sync is already running",
            "task_id": task_name
        }

    # Start background task
    task = asyncio.create_task(_run_initial_sync())
    _running_tasks[task_name] = task
    # Clean up when done
    task.add_done_callback(lambda t: _running_tasks.pop(task_name, None))

    logger.info("initial_sync_triggered_background", task_id=task_name)

    return {
        "status": "initiated",
        "message": "Initial sync started in background. Check /sync/status for progress.",
        "task_id": task_name
    }
