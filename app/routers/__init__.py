"""
API routers.
"""
from app.routers.sales import router as sales_router
from app.routers.orders import router as orders_router
from app.routers.quality import router as quality_router
from app.routers.sync import router as sync_router
from app.routers.health import router as health_router
from app.routers.products import router as products_router
from app.routers.output import router as output_router
from app.routers.sensors import router as sensors_router
from app.routers.inventory import router as inventory_router
from app.routers.line_master_dashboard import router as line_master_dashboard_router
from app.routers.gm_dashboard import router as gm_dashboard_router
from app.routers.qe_dashboard import router as qe_dashboard_router
from app.routers.finance_dashboard import router as finance_dashboard_router
from app.routers.production_analytics import router as production_analytics_router
from app.routers.oee import router as oee_router
from app.routers.export import router as export_router

__all__ = [
    "sales_router",
    "orders_router",
    "quality_router",
    "sync_router",
    "health_router",
    "products_router",
    "output_router",
    "sensors_router",
    "inventory_router",
    "line_master_dashboard_router",
    "gm_dashboard_router",
    "qe_dashboard_router",
    "finance_dashboard_router",
    "production_analytics_router",
    "oee_router",
    "export_router",
]
