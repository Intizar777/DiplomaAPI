"""
Cron job scheduling and tasks.
"""
from app.cron.scheduler import start_scheduler, stop_scheduler
from app.cron.jobs import (
    sync_kpi_task, sync_sales_task, sync_orders_task, sync_quality_task,
    sync_products_task, sync_output_task, sync_sensors_task, sync_inventory_task,
)

__all__ = [
    "start_scheduler",
    "stop_scheduler",
    "sync_kpi_task",
    "sync_sales_task",
    "sync_orders_task",
    "sync_quality_task",
    "sync_products_task",
    "sync_output_task",
    "sync_sensors_task",
    "sync_inventory_task",
]
