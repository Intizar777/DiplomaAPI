"""
Inventory business logic service.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict
from uuid import UUID

from sqlalchemy import select, func, desc, cast, String, outerjoin
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InventorySnapshot, Product, Warehouse
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
import structlog

logger = structlog.get_logger()


class InventoryService:
    """Service for Inventory business logic."""

    def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
        self.db = db
        self.gateway = gateway
    
    async def get_current_inventory(
        self,
        warehouse_code: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> Dict:
        """Get current inventory (latest snapshot)."""
        # Get the latest snapshot date
        latest_date_query = select(func.max(InventorySnapshot.snapshot_date))
        latest_result = await self.db.execute(latest_date_query)
        latest_date = latest_result.scalar()

        if not latest_date:
            return {"items": [], "snapshot_date": None}

        # Join with Product and Warehouse to get enriched data
        query = select(
            InventorySnapshot,
            Product.name.label("product_name"),
            Warehouse.code.label("wh_code")
        ).outerjoin(
            Product, cast(InventorySnapshot.product_id, String) == Product.source_system_id
        ).outerjoin(
            Warehouse, InventorySnapshot.warehouse_id == Warehouse.id
        ).where(
            InventorySnapshot.snapshot_date == latest_date
        ).order_by(InventorySnapshot.warehouse_id, Product.name)

        if warehouse_code:
            query = query.where(Warehouse.code == warehouse_code)
        if product_id:
            query = query.where(InventorySnapshot.product_id == product_id)

        result = await self.db.execute(query)
        rows = result.all()

        return {
            "items": [
                {
                    "product_id": str(row.InventorySnapshot.product_id),
                    "product_name": row.product_name or row.InventorySnapshot.product_name,
                    "warehouse_code": row.wh_code or "",
                    "lot_number": row.InventorySnapshot.lot_number,
                    "quantity": float(row.InventorySnapshot.quantity) if row.InventorySnapshot.quantity else 0,
                    "unit_of_measure": row.InventorySnapshot.unit_of_measure,
                    "last_updated": row.InventorySnapshot.last_updated.isoformat() if row.InventorySnapshot.last_updated else None,
                }
                for row in rows
            ],
            "snapshot_date": latest_date.isoformat() if latest_date else None
        }
    
    async def get_inventory_trends(
        self,
        product_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict:
        """Get inventory trends for a product."""
        query = select(
            InventorySnapshot.snapshot_date,
            func.sum(InventorySnapshot.quantity).label("total_quantity"),
        ).where(
            InventorySnapshot.product_id == product_id
        ).group_by(
            InventorySnapshot.snapshot_date
        ).order_by(
            InventorySnapshot.snapshot_date
        )
        
        if from_date:
            query = query.where(InventorySnapshot.snapshot_date >= from_date)
        if to_date:
            query = query.where(InventorySnapshot.snapshot_date <= to_date)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        items = [
            {
                "date": row.snapshot_date.isoformat(),
                "total_quantity": float(row.total_quantity) if row.total_quantity else 0,
            }
            for row in rows
        ]
        
        return {"items": items, "product_id": product_id}
    
    async def _sync_warehouse(self, warehouse_data: dict) -> Optional[UUID]:
        """Sync a warehouse and return its ID."""
        if not warehouse_data:
            return None

        warehouse_id_raw = warehouse_data.get("id")
        try:
            warehouse_id = UUID(warehouse_id_raw) if isinstance(warehouse_id_raw, str) else warehouse_id_raw
        except (ValueError, AttributeError, TypeError):
            logger.warning("invalid_warehouse_id_skipped", raw=warehouse_id_raw)
            return None

        code = warehouse_data.get("code")

        # Try to find existing by code or id
        if code:
            existing = await self.db.execute(
                select(Warehouse).where(Warehouse.code == code)
            )
            warehouse = existing.scalar_one_or_none()
        else:
            warehouse = None

        if not warehouse and warehouse_id:
            existing = await self.db.execute(
                select(Warehouse).where(Warehouse.id == warehouse_id)
            )
            warehouse = existing.scalar_one_or_none()

        if warehouse:
            warehouse.code = code or warehouse.code
            warehouse.name = warehouse_data.get("name", warehouse.name)
            warehouse.location = warehouse_data.get("location", warehouse.location)
            warehouse.capacity = warehouse_data.get("capacity", warehouse.capacity)
            warehouse.is_active = warehouse_data.get("isActive", warehouse.is_active)
            warehouse.source_system_id = warehouse_data.get("sourceSystemId", warehouse.source_system_id)
        else:
            warehouse = Warehouse(
                id=warehouse_id,
                code=code or f"warehouse_{warehouse_id}",
                name=warehouse_data.get("name", ""),
                location=warehouse_data.get("location", ""),
                capacity=warehouse_data.get("capacity"),
                is_active=warehouse_data.get("isActive", True),
                source_system_id=warehouse_data.get("sourceSystemId"),
            )
            self.db.add(warehouse)

        return warehouse.id

    @track_feature_path(feature_name="inventory.sync_from_gateway", log_result=True)
    async def sync_from_gateway(self, from_date=None, to_date=None) -> int:
        """Sync inventory from Gateway (snapshot current state)."""
        logger.info("syncing_inventory_from_gateway")

        inventory_response = await self.gateway.get_inventory()
        logger.info("inventory_fetched_from_gateway", total_items=len(inventory_response.inventory))

        # Get product name map for enrichment
        product_result = await self.db.execute(select(Product.id, Product.name))
        product_names = {row[0]: row[1] for row in product_result.all()}

        records_processed = 0
        batch_size = 50
        batch = []
        snapshot_date = date.today()

        for inventory_item in inventory_response.inventory:
            product_id = inventory_item.productId
            product_name = product_names.get(product_id) if product_id else None

            # Warehouse ID from the inventory item
            warehouse_id = inventory_item.warehouseId

            # Parse last_updated
            last_updated_raw = inventory_item.lastUpdated
            if isinstance(last_updated_raw, str):
                try:
                    last_updated = datetime.fromisoformat(last_updated_raw.replace("Z", "+00:00"))
                except ValueError:
                    last_updated = None
            else:
                last_updated = None

            snapshot = InventorySnapshot(
                id=inventory_item.id,
                product_id=product_id,
                product_name=product_name,
                warehouse_id=warehouse_id,
                lot_number=inventory_item.lotNumber,
                quantity=Decimal(str(inventory_item.quantity)),
                unit_of_measure=None,
                last_updated=last_updated,
                snapshot_date=snapshot_date
            )
            batch.append(snapshot)

            if len(batch) >= batch_size:
                try:
                    self.db.add_all(batch)
                    await self.db.commit()
                    records_processed += len(batch)
                    logger.info("inventory_sync_batch", records_processed=records_processed)
                except Exception as e:
                    await self.db.rollback()
                    logger.error("inventory_sync_batch_error", error=str(e)[:200])
                batch = []

        if batch:
            try:
                self.db.add_all(batch)
                await self.db.commit()
                records_processed += len(batch)
            except Exception as e:
                await self.db.rollback()
                logger.error("inventory_sync_final_batch_error", error=str(e)[:200])

        log_data_flow(
            source="inventory_service",
            target="database",
            operation="sync_insert",
            records_count=records_processed,
        )
        logger.info("inventory_sync_completed", records_processed=records_processed)
        return records_processed

    async def upsert_from_event(self, payload: "InventoryUpdatedPayload", event_id: str = None) -> None:
        """Upsert inventory snapshot from event. Idempotent by event_id or (product_id, warehouse_code)."""
        from app.messaging.schemas import InventoryUpdatedPayload
        from sqlalchemy import and_
        from uuid import UUID

        # First check by event_id if provided (absolute idempotency)
        if event_id:
            result = await self.db.execute(
                select(InventorySnapshot).where(InventorySnapshot.event_id == UUID(event_id))
            )
            snapshot = result.scalar_one_or_none()
            if snapshot:
                logger.info("inventory_skipped_duplicate_event", event_id=event_id)
                return

        result = await self.db.execute(
            select(InventorySnapshot).where(
                and_(
                    InventorySnapshot.product_id == payload.product_id,
                    InventorySnapshot.warehouse_code == payload.warehouse_code,
                )
            )
        )
        snapshot = result.scalar_one_or_none()

        if snapshot:
            snapshot.quantity = Decimal(str(payload.quantity))
            snapshot.last_updated = datetime.utcnow()
            if event_id:
                snapshot.event_id = UUID(event_id)
            logger.info(
                "inventory_updated_from_event",
                product_id=str(payload.product_id),
                warehouse=payload.warehouse_code,
            )
        else:
            snapshot = InventorySnapshot(
                id=payload.id,
                product_id=payload.product_id,
                warehouse_code=payload.warehouse_code,
                quantity=Decimal(str(payload.quantity)),
                snapshot_date=date.today(),
                event_id=UUID(event_id) if event_id else None,
            )
            self.db.add(snapshot)
            logger.info(
                "inventory_inserted_from_event",
                product_id=str(payload.product_id),
                warehouse=payload.warehouse_code,
            )

        await self.db.commit()
