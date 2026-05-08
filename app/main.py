"""
FastAPI application entry point with comprehensive lifecycle logging.
"""
import asyncio
import os
import sys
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

from app.config import settings
from app.database import init_db, close_db
from app.cron import start_scheduler, stop_scheduler
from app.cron.scheduler import run_scheduled_jobs
from app.logging_config import configure_logging
from app.middleware import RequestLoggingMiddleware
from app.messaging import start_consumer, stop_consumer
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
    personnel_router,
)

# Configure structured logging on module load
configure_logging(settings.log_level, use_json=not settings.debug)
logger = structlog.get_logger()


def _get_memory_info() -> dict:
    """Get current process memory usage."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return {
            "rss_mb": round(mem_info.rss / 1024 / 1024, 2),
            "vms_mb": round(mem_info.vms / 1024 / 1024, 2),
        }
    except ImportError:
        return {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with detailed lifecycle logging."""
    # ---- STARTUP PHASE ----
    logger.info(
        "lifecycle_startup_begin",
        phase="startup",
        name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        python_version=sys.version,
        pid=os.getpid(),
    )

    # Initialize database
    try:
        await init_db()
        logger.info(
            "lifecycle_startup_checkpoint",
            phase="startup",
            checkpoint="database_initialized",
        )
    except Exception as e:
        logger.error(
            "lifecycle_startup_failed",
            phase="startup",
            checkpoint="database_initialization",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise

    # Start scheduler
    try:
        start_scheduler()
        # Start the scheduler task in the background
        asyncio.create_task(run_scheduled_jobs())
        logger.info(
            "lifecycle_startup_checkpoint",
            phase="startup",
            checkpoint="scheduler_started",
        )
    except Exception as e:
        logger.error(
            "lifecycle_startup_failed",
            phase="startup",
            checkpoint="scheduler_start",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise

    # Start RabbitMQ consumer
    try:
        await start_consumer()
        logger.info(
            "lifecycle_startup_checkpoint",
            phase="startup",
            checkpoint="rabbitmq_consumer_started",
        )
    except Exception as e:
        logger.error(
            "lifecycle_startup_failed",
            phase="startup",
            checkpoint="rabbitmq_consumer_start",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise

    # Startup complete — mark as ready
    logger.info(
        "lifecycle_startup_complete",
        phase="startup",
        state="ready",
        memory=_get_memory_info(),
    )

    yield

    # ---- SHUTDOWN PHASE ----
    logger.info(
        "lifecycle_shutdown_begin",
        phase="shutdown",
        state="shutting_down",
    )

    # Stop RabbitMQ consumer first
    try:
        await stop_consumer()
        logger.info(
            "lifecycle_shutdown_checkpoint",
            phase="shutdown",
            checkpoint="rabbitmq_consumer_stopped",
        )
    except Exception as e:
        logger.error(
            "lifecycle_shutdown_error",
            phase="shutdown",
            checkpoint="rabbitmq_consumer_stop",
            error_type=type(e).__name__,
            error_message=str(e),
        )

    # Stop scheduler
    try:
        stop_scheduler()
        logger.info(
            "lifecycle_shutdown_checkpoint",
            phase="shutdown",
            checkpoint="scheduler_stopped",
        )
    except Exception as e:
        logger.error(
            "lifecycle_shutdown_error",
            phase="shutdown",
            checkpoint="scheduler_stop",
            error_type=type(e).__name__,
            error_message=str(e),
        )

    # Close database connections
    try:
        await close_db()
        logger.info(
            "lifecycle_shutdown_checkpoint",
            phase="shutdown",
            checkpoint="database_connections_closed",
        )
    except Exception as e:
        logger.error(
            "lifecycle_shutdown_error",
            phase="shutdown",
            checkpoint="database_close",
            error_type=type(e).__name__,
            error_message=str(e),
        )

    logger.info(
        "lifecycle_shutdown_complete",
        phase="shutdown",
        state="terminated",
        memory=_get_memory_info(),
    )


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Dashboard Analytics API for aggregating data from EFKO microservices",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unhandled exceptions with full context and return a generic error."""
    trace_id = getattr(request.state, "trace_id", "unknown")
    tb_str = traceback.format_exc()
    logger.error(
        "unhandled_exception",
        trace_id=trace_id,
        path=request.url.path,
        method=request.method,
        query=str(request.query_params),
        error_type=type(exc).__name__,
        error_message=str(exc),
        traceback=tb_str,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "trace_id": trace_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Log validation errors with request context."""
    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.warning(
        "validation_error",
        trace_id=trace_id,
        path=request.url.path,
        method=request.method,
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "trace_id": trace_id},
    )


# Add request logging middleware (data flow tracking)
app.add_middleware(RequestLoggingMiddleware)

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
app.include_router(personnel_router)


@app.get("/api/v1/docs", include_in_schema=False)
async def swagger_ui():
    """Redirect to main docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get("/api/v1/swagger.json", include_in_schema=False)
async def swagger_json():
    """Return OpenAPI/Swagger JSON schema."""
    from fastapi.openapi.utils import get_openapi
    return JSONResponse(get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description="Dashboard Analytics API for aggregating data from EFKO microservices",
        routes=app.routes,
    ))


@app.get("/api/v1/docs-llm", include_in_schema=False)
async def llm_docs():
    """Return LLM-friendly documentation from OpenAPI spec."""
    from app.utils.llm_docs_formatter import get_llm_docs
    from fastapi.responses import PlainTextResponse
    
    docs = get_llm_docs(
        app,
        include_examples=True,
        include_deprecated=False,
        require_description=True,
    )
    return PlainTextResponse(docs)
