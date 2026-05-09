"""
Output business logic service.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProductionOutput, Product
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
import structlog

logger = structlog.get_logger()


class OutputService:
    """Service for Production Output business logic."""

    def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
        self.db = db
        self.gateway = gateway
    
    async def get_output_summary(
        self,
        from_date: date,
        to_date: date,
        group_by: str = "day"
    ) -> Dict:
        """Get output summary aggregated by day/shift/line."""
        query = select(ProductionOutput).where(
            ProductionOutput.production_date >= from_date,
            ProductionOutput.production_date <= to_date
        ).order_by(ProductionOutput.production_date)
        
        result = await self.db.execute(query)
        outputs = result.scalars().all()
        
        # Aggregate by requested grouping
        aggregated = {}
        for output in outputs:
            if group_by == "shift":
                key = f"{output.production_date}:{output.shift or 'unknown'}"
            elif group_by == "day":
                key = str(output.production_date)
            else:
                key = str(output.production_date)
            
            if key not in aggregated:
                aggregated[key] = {
                    "date": output.production_date,
                    "shift": output.shift if group_by == "shift" else None,
                    "total_quantity": Decimal("0"),
                    "lot_count": 0,
                    "approved_count": 0,
                }
            
            aggregated[key]["total_quantity"] += output.quantity or Decimal("0")
            aggregated[key]["lot_count"] += 1
            if output.quality_status and output.quality_status.lower() == "approved":
                aggregated[key]["approved_count"] += 1
        
        return {
            "items": list(aggregated.values()),
            "period_from": from_date,
            "period_to": to_date,
            "group_by": group_by
        }
    
    async def get_output_by_shift(
        self,
        from_date: date,
        to_date: date,
        production_line: Optional[str] = None
    ) -> Dict:
        """Get output grouped by shift for line chart."""
        query = select(
            ProductionOutput.production_date,
            ProductionOutput.shift,
            func.sum(ProductionOutput.quantity).label("total_quantity"),
            func.count(ProductionOutput.id).label("lot_count")
        ).where(
            ProductionOutput.production_date >= from_date,
            ProductionOutput.production_date <= to_date
        ).group_by(
            ProductionOutput.production_date,
            ProductionOutput.shift
        ).order_by(
            ProductionOutput.production_date,
            ProductionOutput.shift
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        items = [
            {
                "date": row.production_date,
                "shift": row.shift or "unknown",
                "total_quantity": float(row.total_quantity or 0),
                "lot_count": row.lot_count
            }
            for row in rows
        ]
        
        return {
            "items": items,
            "period_from": from_date,
            "period_to": to_date
        }
    
    @track_feature_path(feature_name="output.sync_from_gateway", log_result=True)
    async def sync_from_gateway(
        self,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> int:
        """Sync output data from Gateway."""
        logger.info("syncing_output_from_gateway", from_date=from_date, to_date=to_date)
        
        gateway_data = await self.gateway.get_output(from_date, to_date)
        outputs = gateway_data.get("outputs", [])
        logger.info("output_fetched_from_gateway", total_outputs=len(outputs))
        
        # Get product name map for enrichment
        product_names = {}
        product_result = await self.db.execute(select(Product.id, Product.name))
        product_names = {row[0]: row[1] for row in product_result.all()}
        
        records_processed = 0
        batch_size = 50
        batch = []
        snapshot_date = date.today()
        
        for output_data in outputs:
            # Extract and validate ID from Gateway
            raw_id = output_data.get("id")
            try:
                output_id = UUID(raw_id) if isinstance(raw_id, str) else raw_id
            except (ValueError, AttributeError, TypeError):
                logger.warning("invalid_production_output_id_skipped", raw=raw_id)
                continue

            # Parse production date
            prod_date_raw = output_data.get("productionDate", date.today())
            if isinstance(prod_date_raw, str):
                try:
                    prod_date = date.fromisoformat(prod_date_raw[:10])
                except ValueError:
                    prod_date = date.today()
            else:
                prod_date = prod_date_raw

            product_id = output_data.get("productId")
            product_name = product_names.get(product_id) if product_id else None

            output = ProductionOutput(
                id=output_id,
                order_id=output_data.get("orderId"),
                product_id=product_id,
                product_name=product_name,
                lot_number=output_data.get("lotNumber", ""),
                quantity=Decimal(str(output_data.get("quantity", 0))),
                quality_status=output_data.get("qualityStatus", "").lower() if output_data.get("qualityStatus") else None,
                production_date=prod_date,
                shift=output_data.get("shift"),
                snapshot_date=snapshot_date
            )
            batch.append(output)
            
            if len(batch) >= batch_size:
                try:
                    self.db.add_all(batch)
                    await self.db.commit()
                    records_processed += len(batch)
                    logger.info("output_sync_batch", records_processed=records_processed)
                except Exception as e:
                    await self.db.rollback()
                    logger.error("output_sync_batch_error", error=str(e)[:200])
                batch = []
        
        if batch:
            try:
                self.db.add_all(batch)
                await self.db.commit()
                records_processed += len(batch)
            except Exception as e:
                await self.db.rollback()
                logger.error("output_sync_final_batch_error", error=str(e)[:200])
        
        log_data_flow(
            source="output_service",
            target="database",
            operation="sync_insert",
            records_count=records_processed,
        )
        logger.info("output_sync_completed", records_processed=records_processed)
        return records_processed

    async def upsert_from_event(self, payload: "OutputRecordedPayload", event_id: str = None) -> None:
        """Upsert production output from output.recorded event. Idempotent by event_id or lot_number."""
        from app.messaging.schemas import OutputRecordedPayload

        # First check by event_id if provided (absolute idempotency)
        if event_id:
            result = await self.db.execute(
                select(ProductionOutput).where(ProductionOutput.event_id == UUID(event_id))
            )
            output = result.scalar_one_or_none()
            if output:
                logger.info("output_skipped_duplicate_event", event_id=event_id)
                return

        result = await self.db.execute(
            select(ProductionOutput).where(ProductionOutput.lot_number == payload.lot_number)
        )
        output = result.scalar_one_or_none()

        if output:
            output.quantity = Decimal(str(payload.quantity))
            if payload.order_id:
                output.order_id = payload.order_id
            if event_id:
                output.event_id = UUID(event_id)
            logger.info("output_updated_from_event", lot_number=payload.lot_number)
        else:
            output = ProductionOutput(
                id=payload.id,
                order_id=payload.order_id,
                lot_number=payload.lot_number,
                quantity=Decimal(str(payload.quantity)),
                production_date=date.today(),
                snapshot_date=date.today(),
                event_id=UUID(event_id) if event_id else None,
            )
            self.db.add(output)
            logger.info("output_inserted_from_event", lot_number=payload.lot_number)

        await self.db.commit()
