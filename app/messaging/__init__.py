"""
RabbitMQ messaging module — event consumption and dispatch.
"""
from app.messaging.consumer import start_consumer, stop_consumer

__all__ = ["start_consumer", "stop_consumer"]
