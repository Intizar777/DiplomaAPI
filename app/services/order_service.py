"""
Order business logic service.
"""
from datetime import date, datetime
from typing import Optional, Dict, List
from uuid import UUID, uuid4

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OrderSnapshot, Product
from app.schemas import OrderStatusSummaryResponse, OrderListResponse, OrderDetailResponse
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
from app.config import settings
import structlog

logger = structlog.get_logger()


class OrderService:
    """Service for order business logic."""

    def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
        self.db = db
        self.gateway = gateway
        self.page_size = settings.default_page_size
    
    async def get_status_summary(
        self,
        from_date: date,
        to_date: date,
        production_line: Optional[str] = None
    ) -> OrderStatusSummaryResponse:
        """Get order status summary."""
        query = select(OrderSnapshot).where(
            OrderSnapshot.snapshot_date >= from_date,
            OrderSnapshot.snapshot_date <= to_date
        )
        
        if production_line:
            query = query.where(OrderSnapshot.production_line == production_line)
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        # Count by status
        by_status = {"planned": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
        by_line: Dict[str, Dict[str, int]] = {}
        
        for record in records:
            status = record.status.lower()
            if status in by_status:
                by_status[status] += 1
            
            line = record.production_line or "unknown"
            if line not in by_line:
                by_line[line] = {"planned": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
            if status in by_line[line]:
                by_line[line][status] += 1
        
        return OrderStatusSummaryResponse(
            by_status=by_status,
            by_production_line=by_line,
            period_from=from_date,
            period_to=to_date
        )
    
    async def get_order_list(
        self,
        from_date: date,
        to_date: date,
        status: Optional[str] = None,
        production_line: Optional[str] = None,
        page: int = 1,
        limit: int = None
    ) -> OrderListResponse:
        """Get paginated list of orders."""
        limit = limit or self.page_size
        
        query = select(OrderSnapshot).where(
            OrderSnapshot.snapshot_date >= from_date,
            OrderSnapshot.snapshot_date <= to_date
        )
        
        if status:
            query = query.where(OrderSnapshot.status == status.lower())
        if production_line:
            query = query.where(OrderSnapshot.production_line == production_line)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(desc(OrderSnapshot.snapshot_date))
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        orders = [
            {
                "order_id": str(record.order_id),
                "external_order_id": record.external_order_id,
                "product_id": str(record.product_id),
                "product_name": record.product_name,
                "target_quantity": record.target_quantity,
                "actual_quantity": record.actual_quantity,
                "unit_of_measure": record.unit_of_measure,
                "status": record.status,
                "production_line": record.production_line,
                "planned_start": record.planned_start,
                "planned_end": record.planned_end,
                "actual_start": record.actual_start,
                "actual_end": record.actual_end,
                "snapshot_date": record.snapshot_date
            }
            for record in records
        ]
        
        pages = (total + limit - 1) // limit
        
        return OrderListResponse(
            orders=orders,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )
    
    async def get_order_detail(self, order_id: str) -> Optional[OrderDetailResponse]:
        """Get detailed information about a specific order."""
        query = select(OrderSnapshot).where(
            OrderSnapshot.order_id == order_id
        ).order_by(desc(OrderSnapshot.snapshot_date)).limit(1)
        
        result = await self.db.execute(query)
        record = result.scalar_one_or_none()
        
        if not record:
            return None
        
        return OrderDetailResponse(
            order_id=str(record.order_id),
            external_order_id=record.external_order_id,
            product_id=str(record.product_id),
            product_name=record.product_name,
            target_quantity=record.target_quantity,
            actual_quantity=record.actual_quantity,
            unit_of_measure=record.unit_of_measure,
            status=record.status,
            production_line=record.production_line,
            planned_start=record.planned_start,
            planned_end=record.planned_end,
            actual_start=record.actual_start,
            actual_end=record.actual_end,
            outputs=[]  # Would need to fetch from separate table or Gateway
        )
    
    @track_feature_path(feature_name="orders.sync_from_gateway", log_result=True)
    async def sync_from_gateway(
        self,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> int:
        """Sync orders data from Gateway."""
        logger.info("syncing_orders_from_gateway", from_date=from_date, to_date=to_date)
        
        # Fetch orders from Gateway
        orders_response = await self.gateway.get_orders(from_date, to_date)

        records_processed = 0
        snapshot_date = date.today()
        batch_size = 50

        logger.info("orders_fetched_from_gateway", total_orders=len(orders_response.orders))

        # Load product names for enrichment
        product_names: Dict[UUID, str] = {}
        product_result = await self.db.execute(select(Product.id, Product.name))
        product_names = {row[0]: row[1] for row in product_result.all()}

        batch = []
        for order_item in orders_response.orders:
            # Each sync creates a new snapshot; gateway ID → order_id
            snapshot_id = uuid4()

            # Parse ISO datetime objects
            def parse_dt(val):
                if val:
                    if isinstance(val, str):
                        try:
                            return datetime.fromisoformat(val.replace("Z", "+00:00"))
                        except ValueError:
                            return None
                    return val if isinstance(val, datetime) else None
                return None

            product_id = order_item.productId
            product_name = None
            if product_id:
                try:
                    product_name = product_names.get(UUID(str(product_id)) if not isinstance(product_id, UUID) else product_id)
                except (ValueError, AttributeError, TypeError):
                    pass

            snapshot = OrderSnapshot(
                id=snapshot_id,
                order_id=order_item.id,
                external_order_id=order_item.externalOrderId,
                product_id=product_id,
                product_name=product_name,
                target_quantity=order_item.targetQuantity,
                actual_quantity=order_item.actualQuantity,
                unit_of_measure=None,
                status=order_item.status.lower() if order_item.status else None,
                production_line=order_item.productionLineId,
                planned_start=parse_dt(order_item.plannedStart),
                planned_end=parse_dt(order_item.plannedEnd),
                actual_start=parse_dt(order_item.actualStart),
                actual_end=parse_dt(order_item.actualEnd),
                snapshot_date=snapshot_date
            )
            batch.append(snapshot)
            
            if len(batch) >= batch_size:
                try:
                    self.db.add_all(batch)
                    await self.db.commit()
                    records_processed += len(batch)
                    logger.info("orders_sync_batch", records_processed=records_processed)
                except Exception as e:
                    await self.db.rollback()
                    logger.error("orders_sync_batch_error", error=str(e)[:200])
                batch = []
        
        # Commit remaining records
        if batch:
            try:
                self.db.add_all(batch)
                await self.db.commit()
                records_processed += len(batch)
            except Exception as e:
                await self.db.rollback()
                logger.error("orders_sync_final_batch_error", error=str(e)[:200])
        
        log_data_flow(
            source="order_service",
            target="database",
            operation="sync_insert",
            records_count=records_processed,
        )
        logger.info("orders_sync_completed", records_processed=records_processed)
        return records_processed

    async def upsert_order_from_event(self, payload: "OrderCreatedPayload", event_id: str = None) -> None:
        """Upsert order from order.created event. Idempotent by event_id or order_id."""
        from app.messaging.schemas import OrderCreatedPayload
        from uuid import UUID

        # First check by event_id if provided (absolute idempotency)
        if event_id:
            result = await self.db.execute(
                select(OrderSnapshot).where(OrderSnapshot.event_id == UUID(event_id))
            )
            existing = result.scalar_one_or_none()
            if existing:
                logger.info("order_skipped_duplicate_event", event_id=event_id)
                return

        result = await self.db.execute(
            select(OrderSnapshot).where(OrderSnapshot.order_id == payload.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            if event_id:
                existing.event_id = UUID(event_id)
                await self.db.commit()
            logger.info("order_already_exists_from_event", order_id=str(payload.id))
            return

        snapshot = OrderSnapshot(
            order_id=payload.id,
            external_order_id=payload.external_order_id,
            product_id=payload.product_id,
            status=payload.status.lower(),
            snapshot_date=date.today(),
            event_id=UUID(event_id) if event_id else None,
        )
        self.db.add(snapshot)
        await self.db.commit()
        logger.info("order_inserted_from_event", order_id=str(payload.id))

    async def update_order_status_from_event(self, payload: "OrderStatusUpdatedPayload", event_id: str = None) -> None:
        """Update order status from order.status-updated event. Keyed on event_id or order_id."""
        from app.messaging.schemas import OrderStatusUpdatedPayload
        from uuid import UUID

        # First check by event_id if provided (absolute idempotency)
        if event_id:
            result = await self.db.execute(
                select(OrderSnapshot).where(OrderSnapshot.event_id == UUID(event_id))
            )
            snapshot = result.scalar_one_or_none()
            if snapshot:
                logger.info("order_status_skipped_duplicate_event", event_id=event_id)
                return

        result = await self.db.execute(
            select(OrderSnapshot).where(OrderSnapshot.order_id == payload.id)
        )
        snapshot = result.scalar_one_or_none()

        if snapshot is None:
            # Insert minimal placeholder
            snapshot = OrderSnapshot(
                order_id=payload.id,
                status=payload.status.lower(),
                actual_quantity=payload.actual_quantity,
                actual_start=payload.actual_start,
                actual_end=payload.actual_end,
                snapshot_date=date.today(),
                event_id=UUID(event_id) if event_id else None,
            )
            self.db.add(snapshot)
            logger.info("order_placeholder_inserted_from_event", order_id=str(payload.id))
        else:
            snapshot.status = payload.status.lower()
            if payload.actual_quantity is not None:
                snapshot.actual_quantity = payload.actual_quantity
            if payload.actual_start is not None:
                snapshot.actual_start = payload.actual_start
            if payload.actual_end is not None:
                snapshot.actual_end = payload.actual_end
            if event_id:
                snapshot.event_id = UUID(event_id)
            logger.info("order_status_updated_from_event", order_id=str(payload.id), status=payload.status)

        await self.db.commit()
