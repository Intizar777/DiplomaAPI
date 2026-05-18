"""
Event dispatcher — routes events to handlers based on routing key.
"""
from typing import Any, Callable, Awaitable, Optional

import structlog

logger = structlog.get_logger()

HandlerType = Callable[..., Awaitable[None]]

_REGISTRY: dict[str, HandlerType] = {}


def register(routing_key: str) -> Callable[[HandlerType], HandlerType]:
    """Decorator to register a handler for a routing key."""
    def decorator(func: HandlerType) -> HandlerType:
        _REGISTRY[routing_key] = func
        return func
    return decorator


async def dispatch(routing_key: str, payload: dict[str, Any], event_id: Optional[str] = None) -> None:
    """Dispatch event to registered handler. Log if no handler found."""
    handler = _REGISTRY.get(routing_key)
    if handler is None:
        logger.warning("event_dispatcher_no_handler", routing_key=routing_key)
        return
    await handler(payload, event_id=event_id)
