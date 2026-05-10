"""
Sales business logic service.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Literal, Dict
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AggregatedSales, SalesTrends, SaleRecord, Product, Customer
from app.schemas import (
    SalesSummaryResponse,
    SalesTrendsResponse,
    TopProductsResponse,
    SalesRegionsResponse
)
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
import structlog

logger = structlog.get_logger()


class SalesService:
    """Service for sales business logic."""

    def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
        self.db = db
        self.gateway = gateway

    async def _sync_customer(self, customer_data: dict) -> Optional[UUID]:
        """Sync a customer and return its ID."""
        if not customer_data:
            return None

        customer_id_raw = customer_data.get("id")
        try:
            customer_id = UUID(customer_id_raw) if isinstance(customer_id_raw, str) else customer_id_raw
        except (ValueError, AttributeError, TypeError):
            logger.warning("invalid_customer_id_skipped", raw=customer_id_raw)
            return None

        code = customer_data.get("code")

        # Try to find existing by code or id
        if code:
            existing = await self.db.execute(
                select(Customer).where(Customer.code == code)
            )
            customer = existing.scalar_one_or_none()
        else:
            customer = None

        if not customer and customer_id:
            existing = await self.db.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = existing.scalar_one_or_none()

        if customer:
            customer.code = code or customer.code
            customer.name = customer_data.get("name", customer.name)
            customer.region = customer_data.get("region", customer.region)
            customer.is_active = customer_data.get("isActive", customer.is_active)
            customer.source_system_id = customer_data.get("sourceSystemId", customer.source_system_id)
        else:
            customer = Customer(
                id=customer_id,
                code=code or f"customer_{customer_id}",
                name=customer_data.get("name", ""),
                region=customer_data.get("region", ""),
                is_active=customer_data.get("isActive", True),
                source_system_id=customer_data.get("sourceSystemId"),
            )
            self.db.add(customer)

        return customer.id

    async def _aggregate_from_raw(
        self,
        from_date: date,
        to_date: date,
        group_by: Literal["region", "channel", "product"]
    ) -> List[Dict]:
        """Aggregate sales from raw SaleRecord data."""
        if group_by == "region":
            group_col = SaleRecord.region
        elif group_by == "channel":
            group_col = SaleRecord.channel
        else:
            group_col = SaleRecord.product_id
        
        query = select(
            group_col.label("group_key"),
            func.sum(SaleRecord.quantity).label("total_quantity"),
            func.sum(SaleRecord.amount).label("total_amount"),
            func.count(SaleRecord.id).label("sales_count")
        ).where(
            SaleRecord.sale_date >= from_date,
            SaleRecord.sale_date <= to_date
        ).group_by(group_col).order_by(desc("total_amount"))
        
        result = await self.db.execute(query)
        rows = result.all()
        
        return [
            {
                "group_key": row.group_key or "unknown",
                "total_quantity": row.total_quantity or Decimal("0"),
                "total_amount": row.total_amount or Decimal("0"),
                "sales_count": row.sales_count or 0,
                "avg_order_value": None
            }
            for row in rows
        ]
    
    async def get_sales_summary(
        self,
        from_date: date,
        to_date: date,
        group_by: Literal["region", "channel", "product"] = "region"
    ) -> SalesSummaryResponse:
        """Get aggregated sales summary."""
        query = select(AggregatedSales).where(
            AggregatedSales.period_from == from_date,
            AggregatedSales.period_to == to_date,
            AggregatedSales.group_by_type == group_by
        ).order_by(desc(AggregatedSales.total_amount))
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        if records:
            summary = [
                {
                    "group_key": record.group_key,
                    "total_quantity": record.total_quantity,
                    "total_amount": record.total_amount,
                    "sales_count": record.sales_count,
                    "avg_order_value": record.avg_order_value
                }
                for record in records
            ]
        else:
            # Fallback: aggregate from raw SaleRecord
            summary = await self._aggregate_from_raw(from_date, to_date, group_by)
        
        total_amount = sum(item["total_amount"] for item in summary)
        total_quantity = sum(item["total_quantity"] for item in summary)
        
        return SalesSummaryResponse(
            summary=summary,
            total_amount=total_amount,
            total_quantity=total_quantity,
            period_from=from_date,
            period_to=to_date,
            group_by=group_by
        )
    
    async def get_sales_trends(
        self,
        from_date: date,
        to_date: date,
        interval: Literal["day", "week", "month"] = "day",
        region: Optional[str] = None,
        channel: Optional[str] = None
    ) -> SalesTrendsResponse:
        """Get sales trends over time."""
        query = select(SalesTrends).where(
            SalesTrends.trend_date >= from_date,
            SalesTrends.trend_date <= to_date,
            SalesTrends.interval_type == interval
        ).order_by(SalesTrends.trend_date)
        
        if region:
            query = query.where(SalesTrends.region == region)
        if channel:
            query = query.where(SalesTrends.channel == channel)
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        trends = [
            {
                "trend_date": record.trend_date,
                "total_amount": record.total_amount,
                "total_quantity": record.total_quantity,
                "order_count": record.order_count
            }
            for record in records
        ]
        
        return SalesTrendsResponse(
            trends=trends,
            interval=interval,
            period_from=from_date,
            period_to=to_date,
            region=region,
            channel=channel
        )
    
    async def get_top_products(
        self,
        from_date: date,
        to_date: date,
        limit: int = 10
    ) -> TopProductsResponse:
        """Get top selling products from raw sales data."""
        # Try raw sales first (more accurate with product_name)
        raw_query = select(
            SaleRecord.product_id,
            SaleRecord.product_name,
            func.sum(SaleRecord.quantity).label("total_quantity"),
            func.sum(SaleRecord.amount).label("total_amount"),
            func.count(SaleRecord.id).label("sales_count")
        ).where(
            SaleRecord.sale_date >= from_date,
            SaleRecord.sale_date <= to_date
        ).group_by(
            SaleRecord.product_id,
            SaleRecord.product_name
        ).order_by(desc("total_amount")).limit(limit)
        
        raw_result = await self.db.execute(raw_query)
        raw_rows = raw_result.all()
        
        if raw_rows:
            products = [
                {
                    "product_id": str(row.product_id),
                    "product_name": row.product_name or "",
                    "total_quantity": row.total_quantity,
                    "total_amount": row.total_amount,
                    "sales_count": row.sales_count
                }
                for row in raw_rows
            ]
        else:
            # Fallback to aggregated data
            query = select(AggregatedSales).where(
                AggregatedSales.period_from == from_date,
                AggregatedSales.period_to == to_date,
                AggregatedSales.group_by_type == "product"
            ).order_by(desc(AggregatedSales.total_amount)).limit(limit)
            
            result = await self.db.execute(query)
            records = result.scalars().all()
            
            products = [
                {
                    "product_id": record.group_key,
                    "product_name": "",
                    "total_quantity": record.total_quantity,
                    "total_amount": record.total_amount,
                    "sales_count": record.sales_count
                }
                for record in records
            ]
        
        return TopProductsResponse(
            products=products,
            period_from=from_date,
            period_to=to_date,
            limit=limit
        )
    
    async def get_sales_by_regions(
        self,
        from_date: date,
        to_date: date
    ) -> SalesRegionsResponse:
        """Get sales breakdown by regions."""
        query = select(AggregatedSales).where(
            AggregatedSales.period_from == from_date,
            AggregatedSales.period_to == to_date,
            AggregatedSales.group_by_type == "region"
        ).order_by(desc(AggregatedSales.total_amount))
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        if records:
            total_amount = sum(record.total_amount for record in records) or Decimal("1")
            regions = [
                {
                    "region": record.group_key,
                    "total_quantity": record.total_quantity,
                    "total_amount": record.total_amount,
                    "sales_count": record.sales_count,
                    "percentage": (record.total_amount / total_amount * 100).quantize(Decimal("0.1"))
                }
                for record in records
            ]
        else:
            # Fallback: aggregate from raw SaleRecord
            raw_summary = await self._aggregate_from_raw(from_date, to_date, "region")
            total_amount = sum(item["total_amount"] for item in raw_summary) or Decimal("1")
            regions = [
                {
                    "region": item["group_key"],
                    "total_quantity": item["total_quantity"],
                    "total_amount": item["total_amount"],
                    "sales_count": item["sales_count"],
                    "percentage": (item["total_amount"] / total_amount * 100).quantize(Decimal("0.1"))
                }
                for item in raw_summary
            ]
        
        
        return SalesRegionsResponse(
            regions=regions,
            period_from=from_date,
            period_to=to_date
        )
    
    @track_feature_path(feature_name="sales.sync_from_gateway", log_result=True)
    async def sync_from_gateway(
        self,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> int:
        """Sync sales data from Gateway."""
        logger.info("syncing_sales_from_gateway", from_date=from_date, to_date=to_date)

        period_from = from_date or date.today() - timedelta(days=1)
        period_to = to_date or date.today()

        # Fetch sales summary from Gateway by region
        summary_response = await self.gateway.get_sales_summary(from_date, to_date, "region")

        records_processed = 0
        from sqlalchemy.dialects.postgresql import insert

        for item in summary_response.summary:
            stmt = insert(AggregatedSales).values(
                period_from=period_from,
                period_to=period_to,
                group_by_type="region",
                group_key=item.groupKey,
                total_quantity=Decimal(str(item.totalQuantity)),
                total_amount=Decimal(str(item.totalAmount)),
                sales_count=item.salesCount
            ).on_conflict_do_update(
                index_elements=['period_from', 'period_to', 'group_by_type', 'group_key'],
                set_=dict(
                    total_quantity=Decimal(str(item.totalQuantity)),
                    total_amount=Decimal(str(item.totalAmount)),
                    sales_count=item.salesCount
                )
            )
            await self.db.execute(stmt)
            records_processed += 1

        # Also fetch by channel
        summary_channel_response = await self.gateway.get_sales_summary(from_date, to_date, "channel")

        for item in summary_channel_response.summary:
            stmt = insert(AggregatedSales).values(
                period_from=period_from,
                period_to=period_to,
                group_by_type="channel",
                group_key=item.groupKey,
                total_quantity=Decimal(str(item.totalQuantity)),
                total_amount=Decimal(str(item.totalAmount)),
                sales_count=item.salesCount
            ).on_conflict_do_update(
                index_elements=['period_from', 'period_to', 'group_by_type', 'group_key'],
                set_=dict(
                    total_quantity=Decimal(str(item.totalQuantity)),
                    total_amount=Decimal(str(item.totalAmount)),
                    sales_count=item.salesCount
                )
            )
            await self.db.execute(stmt)
            records_processed += 1
        
        # Also sync raw sales data for product-level analytics
        try:
            sales_response = await self.gateway.get_sales(from_date, to_date)

            if sales_response.sales:
                # Get product name map for enrichment
                product_result = await self.db.execute(select(Product.id, Product.name))
                product_names = {row[0]: row[1] for row in product_result.all()}

                batch_size = 50
                batch = []
                snapshot_date = date.today()

                for sale_item in sales_response.sales:
                    product_id = sale_item.productId
                    product_name = product_names.get(product_id) if product_id else None

                    # Parse sale_date
                    sale_date_raw = sale_item.saleDate
                    if isinstance(sale_date_raw, str):
                        try:
                            parsed_sale_date = date.fromisoformat(sale_date_raw[:10])
                        except ValueError:
                            parsed_sale_date = date.today()
                    else:
                        parsed_sale_date = sale_date_raw.date() if hasattr(sale_date_raw, 'date') else sale_date_raw

                    sale_record = SaleRecord(
                        id=sale_item.id,
                        external_id=sale_item.externalId,
                        product_id=product_id,
                        product_name=product_name,
                        customer_id=sale_item.customerId,
                        customer_name=None,
                        quantity=Decimal(str(sale_item.quantity)),
                        amount=Decimal(str(sale_item.amount)),
                        sale_date=parsed_sale_date,
                        region=sale_item.region,
                        channel=sale_item.channel.lower() if sale_item.channel else None,
                        snapshot_date=snapshot_date
                    )
                    batch.append(sale_record)

                    if len(batch) >= batch_size:
                        try:
                            self.db.add_all(batch)
                            await self.db.commit()
                            records_processed += len(batch)
                        except Exception as e:
                            await self.db.rollback()
                            logger.error("sales_raw_batch_error", error=str(e)[:200])
                        batch = []

                if batch:
                    try:
                        self.db.add_all(batch)
                        await self.db.commit()
                        records_processed += len(batch)
                    except Exception as e:
                        await self.db.rollback()
                        logger.error("sales_raw_final_batch_error", error=str(e)[:200])
        except Exception as e:
            logger.error("sales_raw_sync_error", error=str(e)[:200])
        
        # Aggregate from raw SaleRecord into AggregatedSales if summary was empty
        if records_processed > 0:
            try:
                for group_type in ["region", "channel"]:
                    group_col = SaleRecord.region if group_type == "region" else SaleRecord.channel
                    
                    agg_query = select(
                        group_col.label("group_key"),
                        func.sum(SaleRecord.quantity).label("total_quantity"),
                        func.sum(SaleRecord.amount).label("total_amount"),
                        func.count(SaleRecord.id).label("sales_count")
                    ).where(
                        SaleRecord.sale_date >= period_from,
                        SaleRecord.sale_date <= period_to
                    ).group_by(group_col)
                    
                    agg_result = await self.db.execute(agg_query)
                    agg_rows = agg_result.all()
                    
                    for row in agg_rows:
                        if not row.group_key:
                            continue
                        aggregated = AggregatedSales(
                            period_from=period_from,
                            period_to=period_to,
                            group_by_type=group_type,
                            group_key=row.group_key,
                            total_quantity=row.total_quantity or Decimal("0"),
                            total_amount=row.total_amount or Decimal("0"),
                            sales_count=row.sales_count or 0
                        )
                        self.db.add(aggregated)
                    
                    if agg_rows:
                        logger.info(
                            "sales_aggregated_from_raw",
                            group_by=group_type,
                            groups=len(agg_rows)
                        )
                
                await self.db.commit()
            except Exception as e:
                await self.db.rollback()
                logger.error("sales_aggregation_error", error=str(e)[:200])
        
        await self.db.commit()
        log_data_flow(
            source="sales_service",
            target="database",
            operation="sync_insert",
            records_count=records_processed,
        )
        logger.info("sales_sync_completed", records_processed=records_processed)
        return records_processed

    async def upsert_sale_from_event(self, payload: "SaleRecordedPayload", event_id: str = None) -> None:
        """Upsert sale record from sale.recorded event. Idempotent by event_id or external_id/id."""
        from app.messaging.schemas import SaleRecordedPayload

        # First check by event_id if provided (absolute idempotency)
        if event_id:
            result = await self.db.execute(
                select(SaleRecord).where(SaleRecord.event_id == UUID(event_id))
            )
            record = result.scalar_one_or_none()
            if record:
                logger.info("sale_skipped_duplicate_event", event_id=event_id)
                return

        if payload.external_id:
            result = await self.db.execute(
                select(SaleRecord).where(SaleRecord.external_id == payload.external_id)
            )
        else:
            result = await self.db.execute(
                select(SaleRecord).where(SaleRecord.id == payload.id)
            )

        record = result.scalar_one_or_none()

        # Sync Customer if present
        customer_id = None
        if hasattr(payload, 'customer') and payload.customer:
            customer_id = await self._sync_customer(payload.customer)

        if record:
            record.amount = Decimal(str(payload.amount))
            if payload.channel:
                record.channel = payload.channel.lower()
            if customer_id:
                record.customer_id = customer_id
            if event_id:
                record.event_id = UUID(event_id)
            logger.info("sale_updated_from_event", external_id=payload.external_id)
        else:
            record = SaleRecord(
                id=payload.id,
                external_id=payload.external_id,
                product_id=payload.product_id,
                customer_id=customer_id,
                amount=Decimal(str(payload.amount)),
                channel=payload.channel.lower() if payload.channel else None,
                sale_date=date.today(),
                snapshot_date=date.today(),
                event_id=UUID(event_id) if event_id else None,
            )
            self.db.add(record)
            logger.info("sale_inserted_from_event", external_id=payload.external_id)

        await self.db.commit()
