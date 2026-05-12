"""
Downtime event business logic service.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DowntimeEvent
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import log_data_flow
import structlog

logger = structlog.get_logger()


class DowntimeEventService:
    """Service for downtime event business logic."""

    def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
        self.db = db
        self.gateway = gateway

    async def sync_from_gateway(self, from_date: Optional[date], to_date: Optional[date]) -> int:
        """Sync downtime events from Gateway."""
        if not self.gateway:
            logger.warning("downtime_event_sync_skipped_no_gateway")
            return 0

        logger.info("downtime_event_sync_started", from_date=from_date, to_date=to_date)

        # Fetch from Gateway
        response = await self.gateway.get_downtime_events(from_date, to_date)
        items = response.get("items", [])

        if not items:
            logger.info("downtime_event_sync_no_items", from_date=from_date, to_date=to_date)
            return 0

        # Upsert into DB (on event_id conflict, do nothing for idempotency)
        inserted = 0
        for item in items:
            try:
                event_id = item.get("eventId") or item.get("event_id")

                stmt = insert(DowntimeEvent).values(
                    production_line_id=item.get("productionLineId") or item.get("production_line_id"),
                    reason=item.get("reason", ""),
                    category=item.get("category", "OTHER"),
                    started_at=item.get("startedAt") or item.get("started_at"),
                    ended_at=item.get("endedAt") or item.get("ended_at"),
                    duration_minutes=item.get("durationMinutes") or item.get("duration_minutes"),
                    event_id=event_id,
                ).on_conflict_do_nothing(index_elements=["event_id"])

                result = await self.db.execute(stmt)
                if result.rowcount > 0:
                    inserted += 1

            except Exception as e:
                logger.error(
                    "downtime_event_sync_item_error",
                    item_id=item.get("id"),
                    error_type=type(e).__name__,
                    error=str(e),
                )

        await self.db.commit()

        log_data_flow(
            source="gateway_api",
            target="downtime_event_service",
            operation="sync_downtime_events",
            records_count=inserted,
        )

        logger.info("downtime_event_sync_completed", inserted=inserted)
        return inserted

    async def get_downtime_events(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        production_line_id: Optional[UUID] = None,
        category: Optional[str] = None,
        offset: int = 0,
        limit: int = 20
    ) -> dict:
        """Get downtime events with optional filters."""
        query = select(DowntimeEvent)

        if from_date:
            query = query.where(DowntimeEvent.started_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            query = query.where(DowntimeEvent.started_at <= datetime.combine(to_date, datetime.max.time()))
        if production_line_id:
            query = query.where(DowntimeEvent.production_line_id == production_line_id)
        if category:
            query = query.where(DowntimeEvent.category == category)

        # Get total count
        count_stmt = select(func.count()).select_from(DowntimeEvent)
        if from_date:
            count_stmt = count_stmt.where(DowntimeEvent.started_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            count_stmt = count_stmt.where(DowntimeEvent.started_at <= datetime.combine(to_date, datetime.max.time()))
        if production_line_id:
            count_stmt = count_stmt.where(DowntimeEvent.production_line_id == production_line_id)
        if category:
            count_stmt = count_stmt.where(DowntimeEvent.category == category)

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
                    "production_line_id": str(item.production_line_id) if item.production_line_id else None,
                    "reason": item.reason,
                    "category": item.category,
                    "started_at": item.started_at,
                    "ended_at": item.ended_at,
                    "duration_minutes": item.duration_minutes,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
                for item in items
            ],
            "total": total,
        }

    async def create_downtime_event(
        self,
        production_line_id: Optional[str],
        reason: str,
        category: str,
        started_at: datetime,
        ended_at: Optional[datetime],
        duration_minutes: Optional[int]
    ) -> dict:
        """Create a new downtime event."""
        event = DowntimeEvent(
            production_line_id=UUID(production_line_id) if production_line_id else None,
            reason=reason,
            category=category,
            started_at=started_at,
            ended_at=ended_at,
            duration_minutes=duration_minutes,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        return {
            "id": str(event.id),
            "production_line_id": str(event.production_line_id) if event.production_line_id else None,
            "reason": event.reason,
            "category": event.category,
            "started_at": event.started_at,
            "ended_at": event.ended_at,
            "duration_minutes": event.duration_minutes,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
        }

    async def get_downtime_summary(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> dict:
        """Get aggregated downtime summary by category."""
        query = select(
            DowntimeEvent.category,
            func.sum(DowntimeEvent.duration_minutes).label("total_minutes"),
            func.count(DowntimeEvent.id).label("count"),
        )

        if from_date:
            query = query.where(DowntimeEvent.started_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            query = query.where(DowntimeEvent.started_at <= datetime.combine(to_date, datetime.max.time()))

        query = query.group_by(DowntimeEvent.category)

        result = await self.db.execute(query)
        rows = result.all()

        items = [
            {
                "category": row.category,
                "total_minutes": int(row.total_minutes) if row.total_minutes else 0,
                "count": row.count,
            }
            for row in rows
        ]

        total_events = sum(item["count"] for item in items)
        total_minutes = sum(item["total_minutes"] for item in items)

        return {
            "items": items,
            "total_events": total_events,
            "total_downtime_minutes": total_minutes,
        }
