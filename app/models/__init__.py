"""
SQLAlchemy ORM models.
"""
from app.models.base import Base, SyncStatus
from app.models.kpi import AggregatedKPI
from app.models.sales import AggregatedSales, SalesTrends, SaleRecord
from app.models.orders import OrderSnapshot
from app.models.quality import QualityResult
from app.models.product import Product
from app.models.output import ProductionOutput
from app.models.sensor import SensorReading
from app.models.inventory import InventorySnapshot
from app.models.sync_log import SyncLog, SyncError
from app.models.personnel import Location, ProductionLine, Department, Position, Workstation, Employee
from app.models.reference import UnitOfMeasure, Warehouse, SensorParameter, Sensor, Customer, QualitySpec, LineCapacityPlan
from app.models.analytics import BatchInput, DowntimeEvent, PromoCampaign

__all__ = [
    "Base",
    "SyncStatus",
    "AggregatedKPI",
    "AggregatedSales",
    "SalesTrends",
    "SaleRecord",
    "OrderSnapshot",
    "QualityResult",
    "Product",
    "ProductionOutput",
    "SensorReading",
    "InventorySnapshot",
    "SyncLog",
    "SyncError",
    "Location",
    "ProductionLine",
    "Department",
    "Position",
    "Workstation",
    "Employee",
    "UnitOfMeasure",
    "Warehouse",
    "SensorParameter",
    "Sensor",
    "Customer",
    "QualitySpec",
    "LineCapacityPlan",
    "BatchInput",
    "DowntimeEvent",
    "PromoCampaign",
]
