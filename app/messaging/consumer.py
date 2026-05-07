"""
RabbitMQ event consumer using aio-pika.
"""
import asyncio
import json
import traceback
from typing import Optional

import structlog
from aio_pika import ExchangeType, connect_robust
from aio_pika.abc import AbstractIncomingMessage

from app.config import settings
from app.messaging import dispatcher

logger = structlog.get_logger()

_consumer_task: Optional[asyncio.Task] = None
_stop_event: Optional[asyncio.Event] = None


async def _process_message(message: AbstractIncomingMessage) -> None:
    """Process a single message from the queue."""
    async with message.process(requeue=True, ignore_processed=True):
        try:
            envelope_raw = json.loads(message.body.decode())
            event_id = envelope_raw.get("event_id", "unknown")
            correlation_id = envelope_raw.get("correlation_id", "unknown")
            event_type = envelope_raw.get("event_type", "unknown")

            logger.info(
                "📨 Event received",
                event_id=event_id,
                event_type=event_type,
                routing_key=message.routing_key,
                correlation_id=correlation_id,
            )

            from app.messaging.schemas import EventEnvelope
            envelope = EventEnvelope.model_validate(envelope_raw)

            logger.info(
                "⚙️  Processing event",
                event_id=event_id,
                event_type=event_type,
                routing_key=message.routing_key,
            )

            await dispatcher.dispatch(message.routing_key, envelope.payload, event_id=str(envelope.event_id))

            logger.info(
                "✅ Event completed",
                event_id=event_id,
                event_type=event_type,
                routing_key=message.routing_key,
            )
        except Exception as exc:
            tb_str = traceback.format_exc()
            logger.error(
                "❌ Event processing failed",
                routing_key=message.routing_key,
                event_id=envelope_raw.get("event_id", "unknown") if 'envelope_raw' in locals() else "unknown",
                event_type=envelope_raw.get("event_type", "unknown") if 'envelope_raw' in locals() else "unknown",
                error_type=type(exc).__name__,
                error_message=str(exc),
                traceback=tb_str,
            )
            raise


async def _consume_loop() -> None:
    """Main consumer loop with auto-reconnect."""
    exchange_name = settings.rabbitmq_exchange
    routing_keys = [
        "production.product.created.event",
        "production.product.updated.event",
        "production.order.created.event",
        "production.order.status-updated.event",
        "production.output.recorded.event",
        "production.sale.recorded.event",
        "production.inventory.updated.event",
        "production.quality-result.recorded.event",
    ]

    logger.info(
        "🔗 Connecting to RabbitMQ",
        url=settings.rabbitmq_url,
        reconnect_interval=5,
    )

    connection = await connect_robust(
        settings.rabbitmq_url,
        reconnect_interval=5,
    )
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=settings.rabbitmq_prefetch_count)

        exchange = await channel.declare_exchange(
            exchange_name, ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue(
            f"{settings.rabbitmq_queue_prefix}.production.events",
            durable=True,
        )
        for rk in routing_keys:
            await queue.bind(exchange, routing_key=rk)

        logger.info(
            "🚀 RabbitMQ Consumer Started",
            exchange=exchange_name,
            queue=queue.name,
            routing_keys_count=len(routing_keys),
            prefetch_count=settings.rabbitmq_prefetch_count,
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                if _stop_event and _stop_event.is_set():
                    logger.info("⏹️  Stop event received, consumer shutting down")
                    break
                await _process_message(message)


async def start_consumer() -> None:
    """Start the RabbitMQ consumer background task."""
    global _consumer_task, _stop_event

    if not settings.rabbitmq_enabled:
        logger.info(
            "⚠️  RabbitMQ Consumer Disabled",
            reason="RABBITMQ_ENABLED environment variable is false",
        )
        return

    _stop_event = asyncio.Event()
    _consumer_task = asyncio.create_task(_consume_loop(), name="rabbitmq_consumer")
    logger.info("✨ RabbitMQ Consumer Task Created")


async def stop_consumer() -> None:
    """Stop the RabbitMQ consumer gracefully."""
    global _consumer_task

    if _consumer_task is None or _consumer_task.done():
        return

    logger.info("🛑 Stopping RabbitMQ Consumer...")

    if _stop_event:
        _stop_event.set()

    _consumer_task.cancel()
    try:
        await _consumer_task
    except asyncio.CancelledError:
        pass

    logger.info("🏁 RabbitMQ Consumer Stopped")
