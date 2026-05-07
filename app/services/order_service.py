"""
Order business logic service.
"""
from datetime import date, datetime
from typing import Optional, Dict, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OrderSnapshot
from app.schemas import OrderStatusSummaryResponse, OrderListResponse, OrderDetailResponse
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
from app.config import settings
import structlog

logger = structlog.get_logger()


class OrderService:
    """Service for order business logic."""
    
    def __init__(self, db: AsyncSession, gateway: GatewayClient):
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
        gateway_data = await self.gateway.get_orders(from_date, to_date)
        
        records_processed = 0
        snapshot_date = date.today()
        batch_size = 50
        
        orders = gateway_data.get("orders", [])
        logger.info("orders_fetched_from_gateway", total_orders=len(orders))
        
        batch = []
        for order in orders:
            # Parse ISO datetime strings to datetime objects
            def parse_dt(val):
                if val and isinstance(val, str):
                    try:
                        # Handle ISO format: "2024-12-01T21:12:32.971Z"
                        return datetime.fromisoformat(val.replace("Z", "+00:00"))
                    except ValueError:
                        return None
                return val
            
            snapshot = OrderSnapshot(
                order_id=order.get("id"),
                external_order_id=order.get("externalOrderId"),
                product_id=order.get("productId"),
                product_name=None,
                target_quantity=order.get("targetQuantity"),
                actual_quantity=order.get("actualQuantity"),
                unit_of_measure=order.get("unitOfMeasure"),
                status=order.get("status", "").lower(),
                production_line=order.get("productionLine"),
                planned_start=parse_dt(order.get("plannedStart")),
                planned_end=parse_dt(order.get("plannedEnd")),
                actual_start=parse_dt(order.get("actualStart")),
                actual_end=parse_dt(order.get("actualEnd")),
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
