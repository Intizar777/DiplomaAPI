"""
FastAPI middleware for comprehensive HTTP request/response logging.

Captures data flow: requests entering and responses leaving the application.
Also tracks resource utilization (memory) per request for anomaly detection.
"""
import os
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

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


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs every HTTP request and response with timing,
    status codes, and data flow metrics.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate trace_id for request correlation
        trace_id = str(uuid.uuid4())[:16]
        structlog.contextvars.bind_contextvars(trace_id=trace_id)
        request.state.trace_id = trace_id

        start_time = time.perf_counter()
        client_host = request.client.host if request.client else "unknown"

        # Log request entry (data flow: inbound)
        logger.info(
            "http_request_started",
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            query=str(request.query_params),
            client_host=client_host,
            user_agent=request.headers.get("user-agent", "unknown"),
            content_type=request.headers.get("content-type"),
            content_length=request.headers.get("content-length"),
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            # Log unhandled exception at middleware level
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "http_request_failed",
                trace_id=trace_id,
                method=request.method,
                path=request.url.path,
                elapsed_ms=round(elapsed_ms, 2),
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Trace-Id"] = trace_id

        # Log response (data flow: outbound)
        logger.info(
            "http_request_completed",
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            elapsed_ms=round(elapsed_ms, 2),
            response_content_type=response.headers.get("content-type"),
            response_content_length=response.headers.get("content-length"),
            memory=_get_memory_info(),
        )

        structlog.contextvars.unbind_contextvars("trace_id")
        return response
