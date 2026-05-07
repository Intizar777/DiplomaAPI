"""
Event dispatcher — routes events to handlers based on routing key.
"""
from typing import Callable, Awaitable

import structlog

logger = structlog.get_logger()

_REGISTRY: dict[str, Callable[[dict], Awaitable[None]]] = {}


def register(routing_key: str) -> Callable:
    """Decorator to register a handler for a routing key."""
    def decorator(func: Callable) -> Callable:
        _REGISTRY[routing_key] = func
        return func
    return decorator


async def dispatch(routing_key: str, payload: dict, event_id: str = None) -> None:
    """Dispatch event to registered handler. Log if no handler found."""
    handler = _REGISTRY.get(routing_key)
    if handler is None:
        logger.warning("event_dispatcher_no_handler", routing_key=routing_key)
        return
    await handler(payload, event_id=event_id)
