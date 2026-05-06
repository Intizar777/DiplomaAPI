"""
Inventory business logic service.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InventorySnapshot, Product
from app.services.gateway_client import GatewayClient
import structlog

logger = structlog.get_logger()


class InventoryService:
    """Service for Inventory business logic."""
    
    def __init__(self, db: AsyncSession, gateway: GatewayClient):
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
        
        # Join with Product to get product_name
        query = select(
            InventorySnapshot,
            Product.name.label("product_name")
        ).outerjoin(
            Product, InventorySnapshot.product_id == Product.id
        ).where(
            InventorySnapshot.snapshot_date == latest_date
        ).order_by(InventorySnapshot.warehouse_code, Product.name)
        
        if warehouse_code:
            query = query.where(InventorySnapshot.warehouse_code == warehouse_code)
        if product_id:
            query = query.where(InventorySnapshot.product_id == product_id)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        return {
            "items": [
                {
                    "product_id": str(row.InventorySnapshot.product_id),
                    "product_name": row.product_name or row.InventorySnapshot.product_name,
                    "warehouse_code": row.InventorySnapshot.warehouse_code,
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
    
    async def sync_from_gateway(self) -> int:
        """Sync inventory from Gateway (snapshot current state)."""
        logger.info("syncing_inventory_from_gateway")
        
        gateway_data = await self.gateway.get_inventory()
        inventory = gateway_data.get("inventory", [])
        logger.info("inventory_fetched_from_gateway", total_items=len(inventory))
        
        # Get product name map for enrichment
        product_result = await self.db.execute(select(Product.id, Product.name))
        product_names = {row[0]: row[1] for row in product_result.all()}
        
        records_processed = 0
        batch_size = 50
        batch = []
        snapshot_date = date.today()
        
        for item_data in inventory:
            product_id = item_data.get("productId")
            product_name = product_names.get(product_id) if product_id else None
            
            # Parse last_updated
            last_updated_raw = item_data.get("lastUpdated")
            if isinstance(last_updated_raw, str):
                try:
                    last_updated = datetime.fromisoformat(last_updated_raw.replace("Z", "+00:00"))
                except ValueError:
                    last_updated = None
            else:
                last_updated = None
            
            snapshot = InventorySnapshot(
                product_id=product_id,
                product_name=product_name,
                warehouse_code=item_data.get("warehouseCode", ""),
                lot_number=item_data.get("lotNumber"),
                quantity=Decimal(str(item_data.get("quantity", 0))),
                unit_of_measure=item_data.get("unitOfMeasure", ""),
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
        
        logger.info("inventory_sync_completed", records_processed=records_processed)
        return records_processed
