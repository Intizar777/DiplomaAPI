"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import settings
from app.database import init_db, close_db
from app.cron import start_scheduler, stop_scheduler
from app.routers import (
    kpi_router,
    sales_router,
    orders_router,
    quality_router,
    sync_router,
    health_router,
    products_router,
    output_router,
    sensors_router,
    inventory_router,
)
from app.api.v1.reports import router as reports_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(
        "application_starting",
        name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug
    )
    
    # Initialize database
    await init_db()
    logger.info("database_initialized")
    
    # Start scheduler
    start_scheduler()
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    
    # Stop scheduler
    stop_scheduler()
    
    # Close database connections
    await close_db()
    logger.info("database_connections_closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Dashboard Analytics API for aggregating data from EFKO microservices",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(kpi_router)
app.include_router(sales_router)
app.include_router(orders_router)
app.include_router(quality_router)
app.include_router(sync_router)
app.include_router(products_router)
app.include_router(output_router)
app.include_router(sensors_router)
app.include_router(inventory_router)
app.include_router(reports_router, prefix="/api/v1")


@app.get("/api/v1/docs", include_in_schema=False)
async def swagger_ui():
    """Redirect to main docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")
