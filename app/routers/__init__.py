"""
API routers.
"""
from app.routers.kpi import router as kpi_router
from app.routers.sales import router as sales_router
from app.routers.orders import router as orders_router
from app.routers.quality import router as quality_router
from app.routers.sync import router as sync_router
from app.routers.health import router as health_router
from app.routers.products import router as products_router
from app.routers.output import router as output_router
from app.routers.sensors import router as sensors_router
from app.routers.inventory import router as inventory_router

__all__ = [
    "kpi_router",
    "sales_router",
    "orders_router",
    "quality_router",
    "sync_router",
    "health_router",
    "products_router",
    "output_router",
    "sensors_router",
    "inventory_router",
]
