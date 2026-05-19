"""
RabbitMQ event consumer using aio-pika.
"""
import asyncio
import json
import traceback
import time
from typing import Optional

import structlog
from aio_pika import ExchangeType, connect_robust
from aio_pika.abc import AbstractIncomingMessage
from pydantic import ValidationError

from app.config import settings
from app.messaging import dispatcher

logger = structlog.get_logger()

_consumer_task: Optional[asyncio.Task] = None
_stop_event: Optional[asyncio.Event] = None

_RESTART_DELAY_SECONDS = 5

# Errors caused by malformed/invalid message content — drop without requeue.
_PERMANENT_ERRORS = (json.JSONDecodeError, UnicodeDecodeError, ValidationError)


async def _process_message(message: AbstractIncomingMessage) -> None:
    """Process a single message from the queue."""
    start_time = time.time()
    envelope_raw: Optional[dict] = None

    async with message.process(requeue=True, ignore_processed=True):
        try:
            envelope_raw = json.loads(message.body.decode())
            event_type = envelope_raw.get("event_type", "unknown")
            event_id = envelope_raw.get("event_id", "unknown")
            correlation_id = envelope_raw.get("correlation_id", "unknown")

            logger.info(
                "event_received",
                event_name=event_type,
                event_id=event_id,
                routing_key=message.routing_key,
                correlation_id=correlation_id,
            )

            from app.messaging.schemas import EventEnvelope
            envelope = EventEnvelope.model_validate(envelope_raw)

            await dispatcher.dispatch(message.routing_key or "", envelope.payload, event_id=str(envelope.event_id))

            processing_time = time.time() - start_time
            logger.info(
                "event_processed",
                event_name=event_type,
                event_id=event_id,
                routing_key=message.routing_key,
                processing_time_ms=f"{processing_time * 1000:.2f}",
            )

        except _PERMANENT_ERRORS as exc:
            # Message is malformed and will never succeed — drop it permanently.
            processing_time = time.time() - start_time
            logger.error(
                "event_poison_message_dropped",
                routing_key=message.routing_key,
                event_id=envelope_raw.get("event_id", "unknown") if envelope_raw else "unknown",
                error_type=type(exc).__name__,
                error_message=str(exc),
                processing_time_ms=f"{processing_time * 1000:.2f}",
            )
            await message.nack(requeue=False)

        except Exception as exc:
            # Transient failure (DB unavailable, service error) — requeue for retry.
            processing_time = time.time() - start_time
            logger.error(
                "event_processing_failed",
                event_id=envelope_raw.get("event_id", "unknown") if envelope_raw else "unknown",
                routing_key=message.routing_key,
                error_type=type(exc).__name__,
                error_message=str(exc),
                processing_time_ms=f"{processing_time * 1000:.2f}",
                traceback=traceback.format_exc(),
            )
            raise


async def _consume_loop() -> None:
    """Main consumer loop. Connects, declares topology, and iterates messages."""
    exchange_name = settings.rabbitmq_exchange
    routing_keys = [
        "production.product.created.event",
        "production.product.updated.event",
        "production.order.changed.event",
        "production.batch-input.recorded.event",
        "production.output.recorded.event",
        "production.sale.recorded.event",
        "production.inventory.updated.event",
        "production.quality-result.recorded.event",
        "production.downtime-event.recorded.event",
        "production.sensor-reading.recorded.event",
        "production.sensor.anomaly.event",
    ]

    logger.info(
        "rabbitmq_connecting",
        url=settings.rabbitmq_url,
        reconnect_interval=_RESTART_DELAY_SECONDS,
    )

    connection = await connect_robust(
        settings.rabbitmq_url,
        reconnect_interval=_RESTART_DELAY_SECONDS,
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
            "rabbitmq_consumer_started",
            exchange=exchange_name,
            queue=queue.name,
            routing_keys_count=len(routing_keys),
            prefetch_count=settings.rabbitmq_prefetch_count,
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                if _stop_event and _stop_event.is_set():
                    logger.info("rabbitmq_consumer_stop_requested")
                    break
                await _process_message(message)


async def _consumer_supervisor() -> None:
    """Supervisor that restarts _consume_loop after transient failures."""
    while not (_stop_event and _stop_event.is_set()):
        try:
            await _consume_loop()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if _stop_event and _stop_event.is_set():
                break
            logger.error(
                "rabbitmq_consumer_crashed",
                error_type=type(exc).__name__,
                error_message=str(exc),
                restart_in_seconds=_RESTART_DELAY_SECONDS,
                traceback=traceback.format_exc(),
            )
            await asyncio.sleep(_RESTART_DELAY_SECONDS)

    logger.info("rabbitmq_supervisor_exited")


async def start_consumer() -> None:
    """Start the RabbitMQ consumer background task."""
    global _consumer_task, _stop_event

    if not settings.rabbitmq_enabled:
        logger.info(
            "rabbitmq_consumer_disabled",
            reason="RABBITMQ_ENABLED is false",
        )
        return

    _stop_event = asyncio.Event()
    _consumer_task = asyncio.create_task(_consumer_supervisor(), name="rabbitmq_consumer")
    logger.info("rabbitmq_consumer_task_created")


async def stop_consumer() -> None:
    """Stop the RabbitMQ consumer gracefully."""
    global _consumer_task

    if _consumer_task is None or _consumer_task.done():
        return

    logger.info("rabbitmq_consumer_stopping")

    if _stop_event:
        _stop_event.set()

    _consumer_task.cancel()
    try:
        await _consumer_task
    except asyncio.CancelledError:
        pass

    logger.info("rabbitmq_consumer_stopped")
