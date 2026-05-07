"""
Enhanced structured logging configuration.

Provides rich context capture for:
- Application lifecycle events
- Feature path execution
- Data flow between components
- Error context with full tracebacks
"""
import logging
import sys
from typing import Any, Dict

import structlog


def _add_trace_id(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add trace_id from context if present."""
    trace_id = structlog.contextvars.get_contextvars().get("trace_id")
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict


def _add_service_context(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service name and version to every log entry."""
    from app.config import settings
    event_dict["service"] = settings.app_name
    event_dict["service_version"] = settings.app_version
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with comprehensive processors."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Suppress noisy third-party logs
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _add_trace_id,
            _add_service_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
