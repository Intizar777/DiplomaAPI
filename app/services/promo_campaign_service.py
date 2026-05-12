"""
Promo campaign business logic service.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PromoCampaign, SaleRecord
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import log_data_flow
import structlog

logger = structlog.get_logger()


class PromoCampaignService:
    """Service for promo campaign business logic."""

    def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
        self.db = db
        self.gateway = gateway

    async def sync_from_gateway(self, from_date: Optional[date], to_date: Optional[date]) -> int:
        """Sync promo campaigns from Gateway."""
        if not self.gateway:
            logger.warning("promo_campaign_sync_skipped_no_gateway")
            return 0

        logger.info("promo_campaign_sync_started", from_date=from_date, to_date=to_date)

        # Fetch from Gateway
        response = await self.gateway.get_promo_campaigns(from_date, to_date)
        items = response.get("items", [])

        if not items:
            logger.info("promo_campaign_sync_no_items", from_date=from_date, to_date=to_date)
            return 0

        # Upsert into DB (on event_id conflict, do nothing for idempotency)
        inserted = 0
        for item in items:
            try:
                event_id = item.get("eventId") or item.get("event_id")

                stmt = insert(PromoCampaign).values(
                    name=item.get("name", ""),
                    description=item.get("description"),
                    channel=item.get("channel", "DIRECT"),
                    product_id=item.get("productId") or item.get("product_id"),
                    discount_percent=item.get("discountPercent") or item.get("discount_percent"),
                    start_date=item.get("startDate") or item.get("start_date"),
                    end_date=item.get("endDate") or item.get("end_date"),
                    budget=item.get("budget"),
                    event_id=event_id,
                ).on_conflict_do_nothing(index_elements=["event_id"])

                result = await self.db.execute(stmt)
                if result.rowcount > 0:
                    inserted += 1

            except Exception as e:
                logger.error(
                    "promo_campaign_sync_item_error",
                    item_id=item.get("id"),
                    error_type=type(e).__name__,
                    error=str(e),
                )

        await self.db.commit()

        log_data_flow(
            source="gateway_api",
            target="promo_campaign_service",
            operation="sync_promo_campaigns",
            records_count=inserted,
        )

        logger.info("promo_campaign_sync_completed", inserted=inserted)
        return inserted

    async def get_promo_campaigns(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        channel: Optional[str] = None,
        offset: int = 0,
        limit: int = 20
    ) -> dict:
        """Get promo campaigns with optional filters."""
        query = select(PromoCampaign)

        if from_date:
            query = query.where(PromoCampaign.start_date >= from_date)
        if to_date:
            query = query.where(PromoCampaign.end_date <= to_date)
        if channel:
            query = query.where(PromoCampaign.channel == channel)

        # Get total count
        count_stmt = select(func.count()).select_from(PromoCampaign)
        if from_date:
            count_stmt = count_stmt.where(PromoCampaign.start_date >= from_date)
        if to_date:
            count_stmt = count_stmt.where(PromoCampaign.end_date <= to_date)
        if channel:
            count_stmt = count_stmt.where(PromoCampaign.channel == channel)

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
                    "name": item.name,
                    "description": item.description,
                    "channel": item.channel,
                    "product_id": str(item.product_id) if item.product_id else None,
                    "discount_percent": item.discount_percent,
                    "start_date": item.start_date,
                    "end_date": item.end_date,
                    "budget": item.budget,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
                for item in items
            ],
            "total": total,
        }

    async def create_promo_campaign(
        self,
        name: str,
        description: Optional[str],
        channel: str,
        product_id: Optional[str],
        discount_percent: Optional[Decimal],
        start_date: date,
        end_date: Optional[date],
        budget: Optional[Decimal]
    ) -> dict:
        """Create a new promo campaign."""
        campaign = PromoCampaign(
            name=name,
            description=description,
            channel=channel,
            product_id=UUID(product_id) if product_id else None,
            discount_percent=discount_percent,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
        )
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)

        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "description": campaign.description,
            "channel": campaign.channel,
            "product_id": str(campaign.product_id) if campaign.product_id else None,
            "discount_percent": campaign.discount_percent,
            "start_date": campaign.start_date,
            "end_date": campaign.end_date,
            "budget": campaign.budget,
            "created_at": campaign.created_at,
            "updated_at": campaign.updated_at,
        }

    async def get_effectiveness(self, campaign_id: UUID) -> dict:
        """Calculate campaign effectiveness (ROI, uplift)."""
        # Get campaign
        campaign = await self.db.get(PromoCampaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Sales during campaign period
        campaign_sales_query = select(func.sum(SaleRecord.amount)).where(
            SaleRecord.sale_date >= campaign.start_date,
            SaleRecord.sale_date <= (campaign.end_date or campaign.start_date),
            (SaleRecord.product_id == campaign.product_id) if campaign.product_id else True,
        )
        sales_during = await self.db.scalar(campaign_sales_query) or Decimal("0")

        # Baseline sales (30 days before campaign start)
        baseline_start = campaign.start_date - timedelta(days=30)
        baseline_query = select(func.sum(SaleRecord.amount)).where(
            SaleRecord.sale_date >= baseline_start,
            SaleRecord.sale_date < campaign.start_date,
            (SaleRecord.product_id == campaign.product_id) if campaign.product_id else True,
        )
        baseline_sales = await self.db.scalar(baseline_query) or Decimal("0")

        # Calculate uplift and ROI
        uplift = sales_during - baseline_sales
        budget = campaign.budget or Decimal("0")
        roi = (uplift / budget) if budget > 0 else Decimal("0")
        roi_percent = roi * 100

        cost_per_uplift = None
        if uplift > 0 and budget > 0:
            cost_per_uplift = budget / uplift

        return {
            "campaign_id": str(campaign.id),
            "campaign_name": campaign.name,
            "budget": budget,
            "sales_during_campaign": sales_during,
            "baseline_sales": baseline_sales,
            "uplift": uplift,
            "cost_per_uplift_unit": cost_per_uplift,
            "roi": roi,
            "roi_percent": roi_percent,
        }
