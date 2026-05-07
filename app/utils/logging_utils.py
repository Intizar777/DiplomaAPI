"""
Logging utilities for feature path execution and error context enrichment.

Provides decorators and helpers for:
- Tracking entry/exit/checkpoints in critical paths
- Capturing full exception context (traceback, locals, args)
- Data flow annotations between components
"""
import functools
import inspect
import traceback
from typing import Any, Callable, Dict, Optional

import structlog

logger = structlog.get_logger()


def _safe_serialize(obj: Any) -> Any:
    """Safely serialize an object for logging."""
    try:
        if hasattr(obj, "__dict__"):
            return {
                "type": type(obj).__name__,
                "module": type(obj).__module__,
                "attrs": {
                    k: str(v)[:200]
                    for k, v in obj.__dict__.items()
                    if not k.startswith("_")
                },
            }
        return str(obj)[:500]
    except Exception:
        return "<unserializable>"


def _extract_call_context(
    func: Callable, args: tuple, kwargs: dict
) -> Dict[str, Any]:
    """Extract function call context including args and kwargs names."""
    sig = inspect.signature(func)
    bound = sig.bind_partial(*args, **kwargs)
    bound.apply_defaults()

    context: Dict[str, Any] = {}
    for name, value in bound.arguments.items():
        if name in ("self", "cls", "db"):
            # Skip internal objects
            context[name] = f"<{type(value).__name__}>"
        else:
            context[name] = _safe_serialize(value)
    return context


def track_feature_path(
    feature_name: Optional[str] = None,
    log_checkpoints: bool = False,
    log_result: bool = False,
):
    """
    Decorator that logs feature path execution:
    - entry: function called with arguments
    - checkpoints: (optional) intermediate steps
    - exit: function completed with timing and optional result summary

    Usage:
        @track_feature_path(feature_name="sales_sync")
        async def sync_from_gateway(self, ...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        fname = feature_name or f"{func.__module__}.{func.__qualname__}"

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                call_ctx = _extract_call_context(func, args, kwargs)
                logger.info(
                    "feature_path_entry",
                    feature=fname,
                    function=func.__qualname__,
                    module=func.__module__,
                    arguments=call_ctx,
                )

                try:
                    result = await func(*args, **kwargs)

                    result_summary = None
                    if log_result:
                        if isinstance(result, (list, tuple)):
                            result_summary = {"type": type(result).__name__, "length": len(result)}
                        elif isinstance(result, dict):
                            result_summary = {"type": "dict", "keys": list(result.keys())[:10]}
                        elif hasattr(result, "model_dump"):
                            result_summary = {"type": type(result).__name__, "dict_keys": list(result.model_dump().keys())[:10]}
                        else:
                            result_summary = {"type": type(result).__name__, "repr": str(result)[:200]}

                    logger.info(
                        "feature_path_exit",
                        feature=fname,
                        function=func.__qualname__,
                        status="success",
                        result_summary=result_summary,
                    )
                    return result
                except Exception as exc:
                    _log_exception_with_context(fname, func, args, kwargs, exc)
                    raise

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                call_ctx = _extract_call_context(func, args, kwargs)
                logger.info(
                    "feature_path_entry",
                    feature=fname,
                    function=func.__qualname__,
                    module=func.__module__,
                    arguments=call_ctx,
                )

                try:
                    result = func(*args, **kwargs)
                    logger.info(
                        "feature_path_exit",
                        feature=fname,
                        function=func.__qualname__,
                        status="success",
                    )
                    return result
                except Exception as exc:
                    _log_exception_with_context(fname, func, args, kwargs, exc)
                    raise

            return sync_wrapper

    return decorator


def _log_exception_with_context(
    feature_name: str,
    func: Callable,
    args: tuple,
    kwargs: dict,
    exc: Exception,
) -> None:
    """Log exception with full context: traceback, args, and locals."""
    tb_str = traceback.format_exc()
    call_ctx = _extract_call_context(func, args, kwargs)

    # Try to capture local variables from the traceback
    local_vars: Dict[str, Any] = {}
    tb = exc.__traceback__
    if tb is not None:
        # Walk to the frame where the exception originated
        while tb.tb_next is not None:
            tb = tb.tb_next
        frame = tb.tb_frame
        local_vars = {
            k: str(v)[:200]
            for k, v in frame.f_locals.items()
            if not k.startswith("_") and k != "self"
        }

    logger.error(
        "feature_path_error",
        feature=feature_name,
        function=func.__qualname__,
        module=func.__module__,
        error_type=type(exc).__name__,
        error_message=str(exc),
        arguments=call_ctx,
        local_variables=local_vars,
        traceback=tb_str,
    )


def log_checkpoint(feature: str, checkpoint: str, extra: Optional[Dict[str, Any]] = None):
    """Log a checkpoint within a feature path."""
    data = {"feature": feature, "checkpoint": checkpoint}
    if extra:
        data.update(extra)
    logger.info("feature_path_checkpoint", **data)


def log_data_flow(
    source: str,
    target: str,
    operation: str,
    payload_summary: Optional[Dict[str, Any]] = None,
    records_count: Optional[int] = None,
):
    """
    Log data flowing between components.

    Args:
        source: Source component (e.g., "gateway_client", "sales_service")
        target: Target component (e.g., "database", "response")
        operation: Operation name (e.g., "insert", "transform", "fetch")
        payload_summary: Summary of the data being transferred
        records_count: Number of records if applicable
    """
    log_data = {
        "source": source,
        "target": target,
        "operation": operation,
    }
    if payload_summary is not None:
        log_data["payload_summary"] = payload_summary
    if records_count is not None:
        log_data["records_count"] = records_count
    logger.info("data_flow", **log_data)
