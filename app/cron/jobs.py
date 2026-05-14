"""
Cron job definitions for data synchronization with full error context logging.
"""
import traceback
from datetime import date, timedelta
from decimal import Decimal
import structlog

from app.database import AsyncSessionLocal
from app.models import SyncLog, SyncStatus
from app.services import GatewayClient, KPIService, SalesService, OrderService, QualityService, ProductService, OutputService, SensorService, InventoryService
from app.config import settings
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

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
    method_name: str = "sync_from_gateway",
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
                    from_date=from_date.isoformat() if from_date else None,
                    to_date=to_date.isoformat() if to_date else None,
                )
                records = await getattr(service, method_name)(from_date, to_date)
            else:
                logger.info(
                    "sync_task_checkpoint",
                    task=task_name,
                    checkpoint="incremental_sync",
                    mode="incremental",
                    from_date=from_date.isoformat() if from_date else None,
                    to_date=to_date.isoformat() if to_date else None,
                )
                records = await getattr(service, method_name)(from_date, to_date)

            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
            logger.info(
                "sync_task_completed",
                task=task_name,
                phase="exit",
                status="success",
                records_processed=records,
            )
            return records
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
    return await _run_sync_task(
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
    return await _run_sync_task(
        task_name="kpi_per_line",
        model_class=AggregatedKPI,
        service_class=KPIService,
        from_date=from_date,
        to_date=to_date,
        method_name="sync_kpi_per_line",
    )


async def sync_sales_task():
    """Sync sales data from Gateway."""
    from_date = date.today() - timedelta(days=30)  # Exactly 1 month ago
    to_date = date.today()

    from app.models import AggregatedSales
    return await _run_sync_task(
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
    return await _run_sync_task(
        task_name="orders",
        model_class=OrderSnapshot,
        service_class=OrderService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_quality_task():
    """Sync quality data from Gateway."""
    from_date = date.today() - timedelta(days=7)
    to_date = date.today()

    from app.models import QualityResult
    return await _run_sync_task(
        task_name="quality",
        model_class=QualityResult,
        service_class=QualityService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_products_task():
    """Sync products from Gateway (full upsert each time)."""
    from app.models import Product
    return await _run_sync_task(
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
    return await _run_sync_task(
        task_name="output",
        model_class=ProductionOutput,
        service_class=OutputService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_sensors_task():
    """Sync sensor readings from Gateway."""
    from_date = date.today() - timedelta(days=30)
    to_date = date.today()

    from app.models import SensorReading
    return await _run_sync_task(
        task_name="sensors",
        model_class=SensorReading,
        service_class=SensorService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_inventory_task():
    """Sync inventory from Gateway (snapshot current state)."""
    from app.models import InventorySnapshot
    return await _run_sync_task(
        task_name="inventory",
        model_class=InventorySnapshot,
        service_class=InventoryService,
        full_sync=True,
    )


async def sync_references_task():
    """Sync Level 0 reference tables from Gateway (full upsert each time).

    Each reference type is wrapped in its own try/except so that a failure
    in one (e.g. 404 on a missing endpoint) does not kill the entire task.
    """
    from app.services.reference_sync import upsert_unit_of_measure, upsert_customer, upsert_warehouse, upsert_production_line

    logger.info("sync_task_started", task="references", phase="entry")

    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "references")
        gateway = GatewayClient()
        total = 0
        errors = []

        # UnitOfMeasure
        try:
            count = 0
            gateway_data = await gateway.get_units_of_measure()
            units = gateway_data.unitsOfMeasure
            logger.info("sync_references_units_fetched", count=len(units))
            for unit_data in units:
                unit_data_dict = unit_data.__dict__ if hasattr(unit_data, '__dict__') else unit_data
                await upsert_unit_of_measure(db, unit_data_dict)
                count += 1
            await db.commit()
            total += count
            logger.info("sync_references_units_done", count=count)
        except Exception as e:
            logger.warning("sync_references_units_error", error=str(e)[:200])
            errors.append(f"units: {e}")

        # Customer
        try:
            count = 0
            gateway_data = await gateway.get_customers()
            customers = gateway_data.customers
            logger.info("sync_references_customers_fetched", count=len(customers))
            for customer_data in customers:
                customer_data_dict = customer_data.__dict__ if hasattr(customer_data, '__dict__') else customer_data
                if not customer_data_dict.get("id"):
                    continue
                await upsert_customer(db, customer_data_dict)
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
                warehouse_data_dict = warehouse_data.__dict__ if hasattr(warehouse_data, '__dict__') else warehouse_data
                if not warehouse_data_dict.get("id"):
                    continue
                await upsert_warehouse(db, warehouse_data_dict)
                count += 1
            await db.commit()
            total += count
            logger.info("sync_references_warehouses_done", count=count)
        except Exception as e:
            logger.warning("sync_references_warehouses_error", error=str(e)[:200])
            errors.append(f"warehouses: {e}")

        # ProductionLine
        try:
            count = 0
            gateway_data = await gateway.get_personnel_production_lines()
            lines = gateway_data.productionLines
            logger.info("sync_references_production_lines_fetched", count=len(lines))
            for line_data in lines:
                line_data_dict = line_data.__dict__ if hasattr(line_data, '__dict__') else line_data
                if not line_data_dict.get("id"):
                    continue
                await upsert_production_line(db, line_data_dict)
                count += 1
            await db.commit()
            total += count
            logger.info("sync_references_production_lines_done", count=count)
        except Exception as e:
            logger.warning("sync_references_production_lines_error", error=str(e)[:200])
            errors.append(f"production_lines: {e}")

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
        return total


async def sync_batch_inputs_task():
    """Sync batch inputs from Gateway."""
    from_date = date.today() - timedelta(days=7)
    to_date = date.today()

    from app.models import BatchInput
    from app.services import BatchInputService

    return await _run_sync_task(
        task_name="batch_inputs",
        model_class=BatchInput,
        service_class=BatchInputService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_downtime_events_task():
    """Sync downtime events from Gateway."""
    from_date = date.today() - timedelta(days=7)
    to_date = date.today()

    from app.models import DowntimeEvent
    from app.services import DowntimeEventService

    return await _run_sync_task(
        task_name="downtime_events",
        model_class=DowntimeEvent,
        service_class=DowntimeEventService,
        from_date=from_date,
        to_date=to_date,
    )


async def sync_promo_campaigns_task():
    """Sync promo campaigns from Gateway."""
    from_date = date.today() - timedelta(days=30)
    to_date = date.today() + timedelta(days=30)

    from app.models import PromoCampaign
    from app.services import PromoCampaignService

    return await _run_sync_task(
        task_name="promo_campaigns",
        model_class=PromoCampaign,
        service_class=PromoCampaignService,
        from_date=from_date,
        to_date=to_date,
    )


async def aggregate_sales_trends_task():
    """Aggregate sale_records into sales_trends for day/week/month intervals."""
    from datetime import datetime
    from sqlalchemy import delete, text
    from app.models.sales import SaleRecord, SalesTrends

    period_days = 35  # slightly wider than sync window to catch week/month boundaries
    from_date = date.today() - timedelta(days=period_days)
    to_date = date.today()

    logger.info(
        "sync_task_started",
        task="aggregate_sales_trends",
        phase="entry",
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
    )

    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "aggregate_sales_trends")

        try:
            total_inserted = 0

            for interval_type in ("day", "week", "month"):
                if interval_type == "day":
                    date_expr = SaleRecord.sale_date
                elif interval_type == "week":
                    date_expr = func.date_trunc("week", SaleRecord.sale_date).cast(SaleRecord.sale_date.type)
                else:
                    date_expr = func.date_trunc("month", SaleRecord.sale_date).cast(SaleRecord.sale_date.type)

                agg_result = await db.execute(
                    select(
                        date_expr.label("trend_date"),
                        SaleRecord.region,
                        SaleRecord.channel,
                        func.sum(SaleRecord.amount).label("total_amount"),
                        func.sum(SaleRecord.quantity).label("total_quantity"),
                        func.count(SaleRecord.id).label("order_count"),
                    )
                    .where(
                        SaleRecord.sale_date >= from_date,
                        SaleRecord.sale_date <= to_date,
                    )
                    .group_by(date_expr, SaleRecord.region, SaleRecord.channel)
                )
                rows = agg_result.all()

                if not rows:
                    continue

                # Delete existing rows for this interval+date range to handle NULL uniqueness
                await db.execute(
                    delete(SalesTrends).where(
                        SalesTrends.interval_type == interval_type,
                        SalesTrends.trend_date >= from_date,
                        SalesTrends.trend_date <= to_date,
                    )
                )

                for row in rows:
                    db.add(SalesTrends(
                        trend_date=row.trend_date,
                        interval_type=interval_type,
                        region=row.region,
                        channel=row.channel,
                        total_amount=row.total_amount or Decimal("0"),
                        total_quantity=row.total_quantity or Decimal("0"),
                        order_count=row.order_count or 0,
                    ))
                    total_inserted += 1

                await db.commit()
                logger.info(
                    "sales_trends_interval_done",
                    interval=interval_type,
                    rows=len(rows),
                )

            await complete_sync_log(db, log, SyncStatus.COMPLETED, total_inserted)
            logger.info(
                "sync_task_completed",
                task="aggregate_sales_trends",
                phase="exit",
                status="success",
                records_processed=total_inserted,
            )
            return total_inserted

        except Exception as e:
            tb_str = traceback.format_exc()
            await db.rollback()
            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=f"{type(e).__name__}: {e}")
            logger.error(
                "sync_task_failed",
                task="aggregate_sales_trends",
                phase="exit",
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=tb_str,
            )
            raise


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

            total_deleted = (
                orders_deleted + quality_deleted + output_deleted +
                sensors_deleted + inventory_deleted + sales_raw_deleted + logs_deleted
            )

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
            return total_deleted
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


async def sync_quality_specs_task():
    """Sync quality specifications from Gateway."""
    from app.models import QualitySpec
    from app.services.reference_sync import upsert_quality_spec

    logger.info("sync_task_started", task="quality_specs", phase="entry")

    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "quality_specs")
        gateway = GatewayClient()

        try:
            count = 0
            gateway_data = await gateway.get_quality_specs()
            specs = gateway_data.get("qualitySpecs", []) if isinstance(gateway_data, dict) else gateway_data.qualitySpecs
            logger.info("sync_quality_specs_fetched", count=len(specs))

            for spec_data in specs:
                spec_data_dict = spec_data.__dict__ if hasattr(spec_data, '__dict__') else spec_data
                if not spec_data_dict.get("productId"):
                    logger.warning("quality_spec_no_product_id_skipped", spec=spec_data_dict)
                    continue
                await upsert_quality_spec(db, spec_data_dict)
                count += 1

            await db.commit()
            logger.info("sync_quality_specs_done", count=count)
            await complete_sync_log(db, log, SyncStatus.COMPLETED, records_processed=count)
            return count

        except Exception as e:
            await db.rollback()
            tb_str = traceback.format_exc()
            logger.error(
                "sync_task_failed",
                task="quality_specs",
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=tb_str,
            )
            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=str(e))
            raise



async def truncate_all_data_task():
    """Truncate all data tables (DANGEROUS - use with caution)."""
    from sqlalchemy import text
    from app.models import (
        AggregatedKPI, AggregatedSales, SalesTrends, SaleRecord,
        OrderSnapshot, QualityResult, Product, ProductionOutput,
        SensorReading, InventorySnapshot, SyncLog, SyncError,
        ProductionLine, UnitOfMeasure, Warehouse, SensorParameter,
        Sensor, Customer, QualitySpec, LineCapacityPlan, KPIConfig,
        BatchInput, DowntimeEvent, PromoCampaign
    )

    logger.warning(
        "truncate_all_data_started",
        phase="entry",
        warning="This will delete ALL data from all tables"
    )

    async with AsyncSessionLocal() as db:
        try:
            tables = [
                # Transactional data (delete first)
                AggregatedKPI, AggregatedSales, SalesTrends, SaleRecord,
                OrderSnapshot, QualityResult, ProductionOutput,
                SensorReading, InventorySnapshot, BatchInput,
                DowntimeEvent, PromoCampaign,
                # Reference data (delete last)
                SyncLog, SyncError, QualitySpec, Sensor,
                Product, SensorParameter, Customer, Warehouse,
                UnitOfMeasure, LineCapacityPlan, KPIConfig,
                ProductionLine,
            ]

            total_deleted = 0
            for table_model in tables:
                table_name = table_model.__tablename__
                try:
                    result = await db.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
                    await db.commit()
                    logger.info("truncate_table_done", table=table_name)
                except Exception as e:
                    logger.warning("truncate_table_failed", table=table_name, error=str(e))
                    await db.rollback()

            logger.warning(
                "truncate_all_data_completed",
                phase="exit",
                status="success",
                tables_truncated=len(tables)
            )
            return total_deleted

        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(
                "truncate_all_data_failed",
                phase="exit",
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=tb_str,
            )
            raise


# Initial sync tasks (full data load without time restrictions)

async def initial_sync_kpi_task():
    """Full KPI sync from 2024-01 to today (no time restrictions)."""
    from app.models import AggregatedKPI
    return await _run_sync_task(
        task_name="initial_sync_kpi",
        model_class=AggregatedKPI,
        service_class=KPIService,
        full_sync=True,
        method_name="sync_from_gateway",
    )


async def initial_sync_kpi_per_line_task():
    """Full KPI per line sync from 2024-01 to today (no time restrictions)."""
    from app.models import AggregatedKPI
    return await _run_sync_task(
        task_name="initial_sync_kpi_per_line",
        model_class=AggregatedKPI,
        service_class=KPIService,
        full_sync=True,
        method_name="sync_kpi_per_line",
    )


async def initial_sync_sales_task():
    """Full sales sync from 2024-01 to today (no time restrictions)."""
    from app.models import AggregatedSales
    return await _run_sync_task(
        task_name="initial_sync_sales",
        model_class=AggregatedSales,
        service_class=SalesService,
        full_sync=True,
    )


async def initial_sync_orders_task():
    """Full orders sync from 2024-01 to today (no time restrictions)."""
    from app.models import OrderSnapshot
    return await _run_sync_task(
        task_name="initial_sync_orders",
        model_class=OrderSnapshot,
        service_class=OrderService,
        full_sync=True,
    )


async def initial_sync_quality_task():
    """Full quality sync from 2024-01 to today (no time restrictions)."""
    from app.models import QualityResult
    return await _run_sync_task(
        task_name="initial_sync_quality",
        model_class=QualityResult,
        service_class=QualityService,
        full_sync=True,
    )


async def initial_sync_output_task():
    """Full output sync from 2024-01 to today (no time restrictions)."""
    from app.models import ProductionOutput
    return await _run_sync_task(
        task_name="initial_sync_output",
        model_class=ProductionOutput,
        service_class=OutputService,
        full_sync=True,
    )


async def initial_sync_sensors_task():
    """Full sensor sync from 2024-01 to today (no time restrictions)."""
    from app.models import SensorReading
    return await _run_sync_task(
        task_name="initial_sync_sensors",
        model_class=SensorReading,
        service_class=SensorService,
        full_sync=True,
    )


async def initial_sync_inventory_task():
    """Full inventory sync from 2024-01 to today (no time restrictions)."""
    from app.models import InventoryLevel
    return await _run_sync_task(
        task_name="initial_sync_inventory",
        model_class=InventoryLevel,
        service_class=InventoryService,
        full_sync=True,
    )


async def initial_sync_batch_inputs_task():
    """Full batch inputs sync (no time restrictions, limit 100)."""
    from app.models import BatchInput
    from app.services import BatchInputService

    async with AsyncSessionLocal() as db:
        gateway = GatewayClient()
        service = BatchInputService(db, gateway)
        
        logger.info("initial_sync_batch_inputs_started", phase="entry")
        try:
            response = await gateway.get_batch_inputs()
            items = response.get("items", [])
            
            if not items:
                logger.info("initial_sync_batch_inputs_no_items")
                return 0
            
            inserted = 0
            for item in items:
                try:
                    from datetime import datetime
                    import dateutil.parser as dateutil_parser
                    
                    item_id = item.get("id")
                    input_date_str = item.get("inputDate")
                    input_date = dateutil_parser.isoparse(input_date_str) if input_date_str else None
                    
                    stmt = insert(BatchInput).values(
                        id=item_id,
                        order_id=item.get("orderId"),
                        product_id=item.get("productId"),
                        quantity=item.get("quantity"),
                        input_date=input_date,
                    ).on_conflict_do_nothing(index_elements=["id"])
                    
                    result = await db.execute(stmt)
                    if result.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    await db.rollback()
                    logger.error("initial_sync_batch_inputs_item_error", error=str(e))
            
            await db.commit()
            logger.info("initial_sync_batch_inputs_completed", records_inserted=inserted)
            return inserted
        except Exception as e:
            logger.error("initial_sync_batch_inputs_failed", error=str(e))
            raise


async def initial_sync_downtime_events_task():
    """Full downtime events sync (no time restrictions, limit 100)."""
    from app.models import DowntimeEvent
    from app.services import DowntimeEventService

    async with AsyncSessionLocal() as db:
        gateway = GatewayClient()
        service = DowntimeEventService(db, gateway)
        
        logger.info("initial_sync_downtime_events_started", phase="entry")
        try:
            response = await gateway.get_downtime_events()
            items = response.get("items", [])
            
            if not items:
                logger.info("initial_sync_downtime_events_no_items")
                return 0
            
            inserted = 0
            for item in items:
                try:
                    from datetime import datetime
                    import dateutil.parser as dateutil_parser
                    
                    item_id = item.get("id")
                    started_at_str = item.get("startedAt")
                    ended_at_str = item.get("endedAt")
                    started_at = dateutil_parser.isoparse(started_at_str) if started_at_str else None
                    ended_at = dateutil_parser.isoparse(ended_at_str) if ended_at_str else None
                    
                    # Skip if started_at is missing (required field)
                    if not started_at:
                        continue
                    
                    stmt = insert(DowntimeEvent).values(
                        id=item_id,
                        production_line_id=item.get("productionLineId"),
                        category=item.get("category"),
                        reason=item.get("reason"),
                        started_at=started_at,
                        ended_at=ended_at,
                        duration_minutes=item.get("durationMinutes"),
                    ).on_conflict_do_nothing(index_elements=["id"])
                    
                    result = await db.execute(stmt)
                    if result.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    await db.rollback()
                    logger.error("initial_sync_downtime_events_item_error", error=str(e))
            
            await db.commit()
            logger.info("initial_sync_downtime_events_completed", records_inserted=inserted)
            return inserted
        except Exception as e:
            logger.error("initial_sync_downtime_events_failed", error=str(e))
            raise


async def initial_sync_promo_campaigns_task():
    """Full promo campaigns sync (no time restrictions, limit 100)."""
    from app.models import PromoCampaign
    from app.services import PromoCampaignService

    async with AsyncSessionLocal() as db:
        gateway = GatewayClient()
        service = PromoCampaignService(db, gateway)
        
        logger.info("initial_sync_promo_campaigns_started", phase="entry")
        try:
            response = await gateway.get_promo_campaigns()
            items = response.get("items", [])
            
            if not items:
                logger.info("initial_sync_promo_campaigns_no_items")
                return 0
            
            inserted = 0
            for item in items:
                try:
                    from datetime import datetime
                    import dateutil.parser as dateutil_parser
                    
                    item_id = item.get("id")
                    start_date_str = item.get("startDate")
                    end_date_str = item.get("endDate")
                    start_date = dateutil_parser.isoparse(start_date_str) if start_date_str else None
                    end_date = dateutil_parser.isoparse(end_date_str) if end_date_str else None
                    
                    stmt = insert(PromoCampaign).values(
                        id=item_id,
                        name=item.get("name", ""),
                        product_id=item.get("productId"),
                        channel=item.get("channel"),
                        start_date=start_date,
                        end_date=end_date,
                        discount_percent=item.get("discountPercent"),
                    ).on_conflict_do_nothing(index_elements=["id"])
                    
                    result = await db.execute(stmt)
                    if result.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    await db.rollback()
                    logger.error("initial_sync_promo_campaigns_item_error", error=str(e))
            
            await db.commit()
            logger.info("initial_sync_promo_campaigns_completed", records_inserted=inserted)
            return inserted
        except Exception as e:
            logger.error("initial_sync_promo_campaigns_failed", error=str(e))
            raise


async def initial_sync_task():
    """Run all initial sync tasks in order."""
    tasks = [
        ("references", sync_references_task),
        ("products", sync_products_task),
        ("quality_specs", sync_quality_specs_task),
        ("initial_sync_kpi", initial_sync_kpi_task),
        ("initial_sync_kpi_per_line", initial_sync_kpi_per_line_task),
        ("initial_sync_sales", initial_sync_sales_task),
        ("initial_sync_orders", initial_sync_orders_task),
        ("initial_sync_quality", initial_sync_quality_task),
        ("initial_sync_output", initial_sync_output_task),
        ("initial_sync_sensors", initial_sync_sensors_task),
        ("initial_sync_inventory", initial_sync_inventory_task),
        ("initial_sync_batch_inputs", initial_sync_batch_inputs_task),
        ("initial_sync_downtime_events", initial_sync_downtime_events_task),
        ("initial_sync_promo_campaigns", initial_sync_promo_campaigns_task),
        ("aggregate_sales_trends", aggregate_sales_trends_task),
    ]
    
    total = 0
    for task_name, task_func in tasks:
        try:
            logger.info("initial_sync_task_running", task=task_name)
            result = await task_func()
            total += result if result else 0
            logger.info("initial_sync_task_completed", task=task_name, records=result)
        except Exception as e:
            logger.error("initial_sync_task_failed", task=task_name, error=str(e))
            raise
    
    return total
