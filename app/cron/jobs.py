"""
Cron job definitions for data synchronization with full error context logging.
"""
import traceback
from datetime import date, timedelta
import structlog

from app.database import AsyncSessionLocal
from app.models import SyncLog, SyncStatus
from app.services import GatewayClient, KPIService, SalesService, OrderService, QualityService, ProductService, OutputService, SensorService, InventoryService, PersonnelService
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


async def _run_sync_task(
    task_name: str,
    model_class,
    service_class,
    from_date: date = None,
    to_date: date = None,
    full_sync: bool = False,
):
    """
    Generic sync task runner with full error context logging.

    Captures:
    - feature path: entry, checkpoints, exit
    - data flow: records processed
    - errors: full traceback, local variables context
    """
    logger.info(
        "sync_task_started",
        task=task_name,
        phase="entry",
        from_date=from_date.isoformat() if from_date else None,
        to_date=to_date.isoformat() if to_date else None,
    )

    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, task_name)
        gateway = GatewayClient()
        service = service_class(db, gateway)

        try:
            if full_sync or not await _has_any_records(model_class):
                logger.info(
                    "sync_task_checkpoint",
                    task=task_name,
                    checkpoint="initial_sync_detected",
                    mode="full",
                )
                records = await service.sync_from_gateway(None, None)
            else:
                logger.info(
                    "sync_task_checkpoint",
                    task=task_name,
                    checkpoint="incremental_sync",
                    mode="incremental",
                    from_date=from_date.isoformat() if from_date else None,
                    to_date=to_date.isoformat() if to_date else None,
                )
                records = await service.sync_from_gateway(from_date, to_date)

            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
            logger.info(
                "sync_task_completed",
                task=task_name,
                phase="exit",
                status="success",
                records_processed=records,
            )
        except Exception as e:
            tb_str = traceback.format_exc()
            error_msg = f"{type(e).__name__}: {e}"

            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=error_msg)

            # Full error context: type, message, traceback, and task metadata
            logger.error(
                "sync_task_failed",
                task=task_name,
                phase="exit",
                status="failed",
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=tb_str,
                from_date=from_date.isoformat() if from_date else None,
                to_date=to_date.isoformat() if to_date else None,
            )
            raise
        finally:
            await gateway.close()


async def sync_kpi_task():
    """Sync KPI data from Gateway (aggregated across all lines)."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    from_date = sunday - timedelta(days=30)
    to_date = sunday

    from app.models import AggregatedKPI
    await _run_sync_task(
        task_name="kpi",
        model_class=AggregatedKPI,
        service_class=KPIService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_kpi_per_line_task():
    """Sync KPI data from Gateway for each production line."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    from_date = sunday - timedelta(days=30)
    to_date = sunday

    from app.models import AggregatedKPI

    logger.info(
        "sync_task_started",
        task="kpi_per_line",
        phase="entry",
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
    )

    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "kpi_per_line")
        gateway = GatewayClient()
        service = KPIService(db, gateway)

        try:
            if not await _has_any_records(AggregatedKPI):
                logger.info(
                    "sync_task_checkpoint",
                    task="kpi_per_line",
                    checkpoint="initial_sync_detected",
                    mode="full",
                )
                records = await service.sync_kpi_per_line(None, None)
            else:
                logger.info(
                    "sync_task_checkpoint",
                    task="kpi_per_line",
                    checkpoint="incremental_sync",
                    mode="incremental",
                    from_date=from_date.isoformat(),
                    to_date=to_date.isoformat(),
                )
                records = await service.sync_kpi_per_line(from_date, to_date)

            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
            logger.info(
                "sync_task_completed",
                task="kpi_per_line",
                phase="exit",
                status="success",
                records_processed=records,
            )
        except Exception as e:
            tb_str = traceback.format_exc()
            error_msg = f"{type(e).__name__}: {e}"

            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=error_msg)

            logger.error(
                "sync_task_failed",
                task="kpi_per_line",
                phase="exit",
                status="failed",
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=tb_str,
                from_date=from_date.isoformat(),
                to_date=to_date.isoformat(),
            )
            raise
        finally:
            await gateway.close()


async def sync_sales_task():
    """Sync sales data from Gateway."""
    from_date = date.today() - timedelta(days=30)  # Exactly 1 month ago
    to_date = date.today()

    from app.models import AggregatedSales
    await _run_sync_task(
        task_name="sales",
        model_class=AggregatedSales,
        service_class=SalesService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_orders_task():
    """Sync orders data from Gateway."""
    from_date = date.today() - timedelta(days=1)
    to_date = date.today()

    from app.models import OrderSnapshot
    await _run_sync_task(
        task_name="orders",
        model_class=OrderSnapshot,
        service_class=OrderService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_quality_task():
    """Sync quality data from Gateway."""
    from_date = date.today() - timedelta(days=1)
    to_date = date.today()

    from app.models import QualityResult
    await _run_sync_task(
        task_name="quality",
        model_class=QualityResult,
        service_class=QualityService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_products_task():
    """Sync products from Gateway (full upsert each time)."""
    from app.models import Product
    await _run_sync_task(
        task_name="products",
        model_class=Product,
        service_class=ProductService,
        full_sync=True,
    )


async def sync_output_task():
    """Sync output data from Gateway."""
    from_date = date.today() - timedelta(days=1)
    to_date = date.today()

    from app.models import ProductionOutput
    await _run_sync_task(
        task_name="output",
        model_class=ProductionOutput,
        service_class=OutputService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_sensors_task():
    """Sync sensor readings from Gateway."""
    from_date = date.today() - timedelta(days=1)
    to_date = date.today()

    from app.models import SensorReading
    await _run_sync_task(
        task_name="sensors",
        model_class=SensorReading,
        service_class=SensorService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_inventory_task():
    """Sync inventory from Gateway (snapshot current state)."""
    from app.models import InventorySnapshot
    await _run_sync_task(
        task_name="inventory",
        model_class=InventorySnapshot,
        service_class=InventoryService,
        full_sync=True,
    )


async def sync_personnel_task():
    """Sync personnel data from Gateway (full upsert each time)."""
    from app.models import PersonnelEmployee
    await _run_sync_task(
        task_name="personnel",
        model_class=PersonnelEmployee,
        service_class=PersonnelService,
        full_sync=True,
    )


async def sync_references_task():
    """Sync Level 0 reference tables from Gateway (full upsert each time).

    Each reference type is wrapped in its own try/except so that a failure
    in one (e.g. 404 on a missing endpoint) does not kill the entire task.
    """
    from app.models import UnitOfMeasure, Warehouse, Customer
    from app.services import ProductService, SensorService
    from datetime import datetime

    logger.info("sync_task_started", task="references", phase="entry")

    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "references")
        gateway = GatewayClient()
        total = 0
        errors = []

        # UnitOfMeasure
        try:
            product_service = ProductService(db, gateway)
            count = 0
            gateway_data = await gateway.get_units_of_measure()
            units = gateway_data.unitsOfMeasure
            logger.info("sync_references_units_fetched", count=len(units))
            for unit_data in units:
                await product_service._sync_unit_of_measure(unit_data)
                count += 1
            await db.commit()
            total += count
            logger.info("sync_references_units_done", count=count)
        except Exception as e:
            logger.warning("sync_references_units_error", error=str(e)[:200])
            errors.append(f"units: {e}")

        # SensorParameter (endpoint may not exist; parameters sync via sensors)
        try:
            sensor_service = SensorService(db, gateway)
            count = 0
            gateway_data = await gateway.get_sensor_parameters()
            params = gateway_data.get("parameters", [])
            logger.info("sync_references_sensor_params_fetched", count=len(params))
            for param_data in params:
                await sensor_service._sync_sensor_parameter(param_data)
                count += 1
            await db.commit()
            total += count
            logger.info("sync_references_sensor_params_done", count=count)
        except Exception as e:
            logger.warning("sync_references_sensor_params_error", error=str(e)[:200])
            errors.append(f"sensor_params: {e}")

        # Customer
        try:
            count = 0
            gateway_data = await gateway.get_customers()
            customers = gateway_data.customers
            logger.info("sync_references_customers_fetched", count=len(customers))
            for customer_data in customers:
                customer_id = customer_data.id
                code = getattr(customer_data, "code", None) or str(customer_id)[:8]
                if not customer_id:
                    continue
                existing = await db.execute(
                    select(Customer).where(Customer.id == customer_id)
                )
                customer = existing.scalar_one_or_none()
                if customer:
                    customer.name = customer_data.name
                    customer.region = getattr(customer_data, "region", "Unknown")
                    customer.is_active = getattr(customer_data, "isActive", True)
                else:
                    db.add(Customer(
                        id=customer_id,
                        code=code,
                        name=customer_data.name,
                        region=getattr(customer_data, "region", "Unknown"),
                        is_active=getattr(customer_data, "isActive", True)
                    ))
                count += 1
            await db.commit()
            total += count
            logger.info("sync_references_customers_done", count=count)
        except Exception as e:
            logger.warning("sync_references_customers_error", error=str(e)[:200])
            errors.append(f"customers: {e}")

        # Warehouse
        try:
            count = 0
            gateway_data = await gateway.get_warehouses()
            warehouses = gateway_data.warehouses
            logger.info("sync_references_warehouses_fetched", count=len(warehouses))
            for warehouse_data in warehouses:
                warehouse_id = warehouse_data.id
                code = warehouse_data.code
                if not warehouse_id:
                    continue
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
                    db.add(Warehouse(
                        id=warehouse_id,
                        code=code,
                        name=warehouse_data.name,
                        location=getattr(warehouse_data, "location", "Unknown"),
                        capacity=getattr(warehouse_data, "capacity", 0),
                        is_active=getattr(warehouse_data, "isActive", True)
                    ))
                count += 1
            await db.commit()
            total += count
            logger.info("sync_references_warehouses_done", count=count)
        except Exception as e:
            logger.warning("sync_references_warehouses_error", error=str(e)[:200])
            errors.append(f"warehouses: {e}")

        # Finalize
        if errors:
            await complete_sync_log(
                db, log, SyncStatus.FAILED,
                records_processed=total,
                error_message="; ".join(errors)
            )
            logger.info(
                "sync_task_completed_with_errors",
                task="references", phase="exit", status="partial",
                records_processed=total, errors=errors
            )
        else:
            await complete_sync_log(db, log, SyncStatus.COMPLETED, total)
            logger.info(
                "sync_task_completed",
                task="references", phase="exit", status="success",
                records_processed=total
            )

        await gateway.close()


async def cleanup_old_data_task():
    """Cleanup old data based on retention settings."""
    from datetime import datetime, timedelta
    from sqlalchemy import delete
    from app.database import AsyncSessionLocal
    from app.models import (
        OrderSnapshot, QualityResult, SyncLog,
        ProductionOutput, SensorReading, InventorySnapshot, SaleRecord,
    )

    logger.info(
        "cleanup_task_started",
        task="cleanup_old_data",
        retention_days=settings.retention_days,
    )

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
                "cleanup_task_completed",
                task="cleanup_old_data",
                orders_deleted=orders_deleted,
                quality_deleted=quality_deleted,
                output_deleted=output_deleted,
                sensors_deleted=sensors_deleted,
                inventory_deleted=inventory_deleted,
                sales_raw_deleted=sales_raw_deleted,
                logs_deleted=logs_deleted,
            )
        except Exception as e:
            await db.rollback()
            tb_str = traceback.format_exc()
            logger.error(
                "cleanup_task_failed",
                task="cleanup_old_data",
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=tb_str,
            )
            raise
