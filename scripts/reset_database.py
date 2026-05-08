#!/usr/bin/env python3
"""
Database reset script - TRUNCATES ALL DATA for testing/development.

⚠️  WARNING: This deletes all data. Use only for testing and development.

Usage:
    python scripts/reset_database.py

This is useful for:
- Testing cron triggers from scratch
- Resetting database to clean state
- Development testing
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import AsyncSessionLocal
import structlog

logger = structlog.get_logger()


async def reset_database():
    """Truncate all tables in the database."""
    # Data tables (operational data)
    data_tables = [
        # Production & Quality
        "production_output",
        "quality_results",
        # Sales & Orders
        "sale_records",
        "aggregated_sales",
        "sales_trends",
        "order_snapshots",
        # Inventory & Sensors
        "inventory_snapshots",
        "sensor_readings",
        # Aggregates
        "aggregated_kpi",
        # Logs
        "sync_logs",
        "sync_errors",
    ]

    # Reference tables (synced from Gateway)
    ref_tables = [
        "products",
        "production_lines",
        "workstations",
        "quality_specs",
        "sensors",
        "sensor_parameters",
        "customers",
        "departments",
        "employees",
        "positions",
        "locations",
        "warehouses",
        "units_of_measure",
    ]

    # Combine both for full reset (re-sync from Gateway)
    tables = data_tables + ref_tables

    logger.warning("database_reset_started", tables_count=len(tables))
    truncated_count = 0

    for table in tables:
        async with AsyncSessionLocal() as db:
            try:
                # Each table gets its own transaction to avoid cascading failures
                await db.execute(text(f"TRUNCATE TABLE \"{table}\" CASCADE"))
                await db.commit()
                logger.info("table_truncated", table=table)
                truncated_count += 1
            except Exception as e:
                # Table might not exist, continue
                error_msg = str(e)
                if "does not exist" in error_msg or "relation" in error_msg:
                    logger.debug("table_not_found", table=table)
                else:
                    logger.warning("table_truncate_error", table=table, error=error_msg)

    logger.info("database_reset_completed", tables_truncated=truncated_count)
    print("\n" + "=" * 60)
    print("✓ DATABASE RESET COMPLETE")
    print("=" * 60)
    print(f"\nTruncated {truncated_count} tables.")
    print("Next cron run will perform full sync from Gateway.")
    print("\n")
    return 0


async def main():
    """Run reset with confirmation."""
    print("\n" + "=" * 60)
    print("⚠️  DATABASE RESET UTILITY")
    print("=" * 60)
    print("\nThis will DELETE ALL DATA from (24 tables):")
    print("\n📊 Data tables:")
    print("  ✓ Production data (production_output)")
    print("  ✓ Quality results")
    print("  ✓ Inventory snapshots")
    print("  ✓ Orders (order_snapshots)")
    print("  ✓ Sales (sale_records, aggregated_sales, sales_trends)")
    print("  ✓ Sensor readings")
    print("  ✓ Aggregated KPI")
    print("  ✓ Sync logs & errors")
    print("\n📋 Reference tables (synced from Gateway):")
    print("  ✓ Products, ProductionLines, Workstations")
    print("  ✓ Sensors, SensorParameters, QualitySpecs")
    print("  ✓ Customers, Employees, Departments, Positions")
    print("  ✓ Locations, Warehouses, UnitsOfMeasure")
    print("\nThis is useful for:")
    print("  ✓ Full reset before re-sync with Gateway")
    print("  ✓ Testing cron triggers from scratch")
    print("  ✓ Development/testing")
    print("\n" + "=" * 60)

    response = input("\nType 'yes' to confirm reset: ").strip().lower()

    if response != "yes":
        print("Cancelled.\n")
        return 0

    return await reset_database()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
