"""
RabbitMQ messaging module — event consumption and dispatch.
"""
from app.messaging.consumer import start_consumer, stop_consumer
from app.messaging import handlers as _  # Import to register handlers

__all__ = ["start_consumer", "stop_consumer"]
