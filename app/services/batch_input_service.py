"""
Batch input business logic service.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BatchInput, ProductionOutput
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import log_data_flow
import structlog

logger = structlog.get_logger()


class BatchInputService:
    """Service for batch input business logic."""

    def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
        self.db = db
        self.gateway = gateway

    async def sync_from_gateway(self, from_date: Optional[date], to_date: Optional[date]) -> int:
        """Sync batch inputs from Gateway."""
        if not self.gateway:
            logger.warning("batch_input_sync_skipped_no_gateway")
            return 0

        logger.info("batch_input_sync_started", from_date=from_date, to_date=to_date)

        # Fetch from Gateway
        response = await self.gateway.get_batch_inputs(from_date, to_date)
        items = response.get("items", [])

        if not items:
            logger.info("batch_input_sync_no_items", from_date=from_date, to_date=to_date)
            return 0

        # Upsert into DB (on event_id conflict, do nothing for idempotency)
        inserted = 0
        for item in items:
            try:
                event_id = item.get("eventId") or item.get("event_id")

                stmt = insert(BatchInput).values(
                    order_id=item.get("orderId") or item.get("order_id"),
                    product_id=item.get("productId") or item.get("product_id"),
                    quantity=item.get("quantity"),
                    input_date=item.get("inputDate") or item.get("input_date"),
                    event_id=event_id,
                ).on_conflict_do_nothing(index_elements=["event_id"])

                result = await self.db.execute(stmt)
                if result.rowcount > 0:
                    inserted += 1

            except Exception as e:
                logger.error(
                    "batch_input_sync_item_error",
                    item_id=item.get("id"),
                    error_type=type(e).__name__,
                    error=str(e),
                )

        await self.db.commit()

        log_data_flow(
            source="gateway_api",
            target="batch_input_service",
            operation="sync_batch_inputs",
            records_count=inserted,
        )

        logger.info("batch_input_sync_completed", inserted=inserted)
        return inserted

    async def get_batch_inputs(
        self,
        order_id: Optional[UUID] = None,
        product_id: Optional[UUID] = None,
        offset: int = 0,
        limit: int = 20
    ) -> dict:
        """Get batch inputs with optional filters."""
        query = select(BatchInput)

        if order_id:
            query = query.where(BatchInput.order_id == order_id)
        if product_id:
            query = query.where(BatchInput.product_id == product_id)

        # Get total count
        count_stmt = select(func.count()).select_from(BatchInput)
        if order_id:
            count_stmt = count_stmt.where(BatchInput.order_id == order_id)
        if product_id:
            count_stmt = count_stmt.where(BatchInput.product_id == product_id)

        total = await self.db.scalar(count_stmt)

        # Get paginated results
        result = await self.db.execute(
            query.offset(offset).limit(limit)
        )
        items = result.scalars().all()

        return {
            "items": [
                {
                    "id": str(item.id),
                    "order_id": str(item.order_id) if item.order_id else None,
                    "product_id": str(item.product_id) if item.product_id else None,
                    "quantity": item.quantity,
                    "input_date": item.input_date,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
                for item in items
            ],
            "total": total,
        }

    async def create_batch_input(self, order_id: Optional[str], product_id: Optional[str], quantity, input_date) -> dict:
        """Create a new batch input record."""
        batch_input = BatchInput(
            order_id=UUID(order_id) if order_id else None,
            product_id=UUID(product_id) if product_id else None,
            quantity=quantity,
            input_date=input_date,
        )
        self.db.add(batch_input)
        await self.db.commit()
        await self.db.refresh(batch_input)

        return {
            "id": str(batch_input.id),
            "order_id": str(batch_input.order_id) if batch_input.order_id else None,
            "product_id": str(batch_input.product_id) if batch_input.product_id else None,
            "quantity": batch_input.quantity,
            "input_date": batch_input.input_date,
            "created_at": batch_input.created_at,
            "updated_at": batch_input.updated_at,
        }

    async def get_yield_ratio(self, order_id: UUID) -> dict:
        """Calculate yield ratio (input to output) for an order."""
        # Sum all inputs for this order
        input_query = select(func.sum(BatchInput.quantity)).where(BatchInput.order_id == order_id)
        total_input = await self.db.scalar(input_query) or 0

        # Sum all outputs for this order
        output_query = select(func.sum(ProductionOutput.quantity)).where(ProductionOutput.order_id == order_id)
        total_output = await self.db.scalar(output_query) or 0

        # Calculate yield percentage
        yield_percent = (total_output / total_input * 100) if total_input > 0 else 0

        # Target yield (hardcoded, can be made configurable)
        target_yield = 86.0

        return {
            "order_id": str(order_id),
            "total_input": total_input,
            "total_output": total_output,
            "yield_percent": yield_percent,
            "target": target_yield,
        }
