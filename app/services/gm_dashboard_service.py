"""
Group Manager Strategic Dashboard service.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.kpi import AggregatedKPI
from app.models.orders import OrderSnapshot
from app.schemas.gm_dashboard import (
    OEEDataPoint,
    OEELineItem,
    OEESummaryResponse,
    PlanExecutionLineItem,
    PlanExecutionResponse,
    DowntimeLineItem,
    DowntimeRankingResponse,
)

logger = structlog.get_logger()

OEE_TARGET = Decimal("75.0")


class GroupManagerDashboardService:
    """Provides strategic dashboard aggregations for Group Managers."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_oee_summary(self, period_days: int) -> OEESummaryResponse:
        """
        Return OEE summary by production line, ranked best-to-worst.

        Reads from AggregatedKPI; uses two passes:
        1. GROUP BY aggregate for avg/sum/count per line.
        2. Raw data points for per-line trend sparklines.
        """
        today = date.today()
        period_from = today - timedelta(days=period_days)

        # Pass 1 — aggregate per line
        agg_query = (
            select(
                AggregatedKPI.product_line_id,
                AggregatedKPI.production_line_name,
                func.avg(AggregatedKPI.oee_estimate).label("avg_oee"),
                func.sum(AggregatedKPI.completed_orders).label("completed_orders"),
                func.sum(AggregatedKPI.total_orders).label("total_orders"),
                func.avg(AggregatedKPI.defect_rate).label("avg_defect_rate"),
                func.count(AggregatedKPI.id).label("data_points"),
            )
            .where(AggregatedKPI.period_from >= period_from)
            .group_by(AggregatedKPI.product_line_id, AggregatedKPI.production_line_name)
            .order_by(func.avg(AggregatedKPI.oee_estimate).desc().nulls_last())
        )
        agg_result = await self.db.execute(agg_query)
        agg_rows = agg_result.all()

        # Pass 2 — raw data points for trend (only non-NULL oee_estimate)
        trend_query = (
            select(
                AggregatedKPI.product_line_id,
                AggregatedKPI.period_from,
                AggregatedKPI.period_to,
                AggregatedKPI.oee_estimate,
            )
            .where(
                AggregatedKPI.period_from >= period_from,
                AggregatedKPI.oee_estimate.isnot(None),
            )
            .order_by(AggregatedKPI.product_line_id, AggregatedKPI.period_from)
        )
        trend_result = await self.db.execute(trend_query)
        trend_rows = trend_result.all()

        # Build trend map keyed by product_line_id (None is a valid key)
        trend_map: Dict[Optional[str], List[OEEDataPoint]] = {}
        for row in trend_rows:
            key = row.product_line_id
            if key not in trend_map:
                trend_map[key] = []
            trend_map[key].append(
                OEEDataPoint(
                    period_from=row.period_from,
                    period_to=row.period_to,
                    oee_value=Decimal(str(row.oee_estimate)).quantize(Decimal("0.01")),
                )
            )

        # Assemble response
        lines: List[OEELineItem] = []
        for row in agg_rows:
            avg_oee = Decimal(str(row.avg_oee or 0)).quantize(Decimal("0.01"))
            vs_target = (avg_oee - OEE_TARGET).quantize(Decimal("0.01"))
            lines.append(
                OEELineItem(
                    production_line=row.production_line_name or row.product_line_id,
                    avg_oee=avg_oee,
                    vs_target_pct=vs_target,
                    completed_orders=int(row.completed_orders or 0),
                    total_orders=int(row.total_orders or 0),
                    avg_defect_rate=Decimal(str(row.avg_defect_rate or 0)).quantize(Decimal("0.01")),
                    data_points=int(row.data_points),
                    trend=trend_map.get(row.product_line_id, []),
                )
            )

        logger.info(
            "oee_summary_calculated",
            period_days=period_days,
            period_from=str(period_from),
            line_count=len(lines),
        )

        return OEESummaryResponse(
            period_days=period_days,
            period_from=period_from,
            period_to=today,
            lines=lines,
            oee_target=OEE_TARGET,
        )

    async def get_plan_execution(
        self,
        date_from: date,
        date_to: date,
    ) -> PlanExecutionResponse:
        """
        Return plan vs actual execution by production line.

        Aggregates OrderSnapshot target/actual quantities and status counts
        grouped by production_line for the requested period.
        """
        query = (
            select(
                OrderSnapshot.production_line,
                func.sum(OrderSnapshot.target_quantity).label("target_quantity"),
                func.sum(OrderSnapshot.actual_quantity).label("actual_quantity"),
                func.count(OrderSnapshot.id).label("total_snapshots"),
                func.sum(
                    case((OrderSnapshot.status == "planned", 1), else_=0)
                ).label("orders_planned"),
                func.sum(
                    case((OrderSnapshot.status == "in_progress", 1), else_=0)
                ).label("orders_in_progress"),
                func.sum(
                    case((OrderSnapshot.status == "completed", 1), else_=0)
                ).label("orders_completed"),
                func.sum(
                    case((OrderSnapshot.status == "cancelled", 1), else_=0)
                ).label("orders_cancelled"),
            )
            .where(
                OrderSnapshot.snapshot_date >= date_from,
                OrderSnapshot.snapshot_date <= date_to,
            )
            .group_by(OrderSnapshot.production_line)
            .order_by(OrderSnapshot.production_line)
        )
        result = await self.db.execute(query)
        rows = result.all()

        # Build production line UUID -> name map
        from app.models.reference import ProductionLine
        line_result = await self.db.execute(select(ProductionLine.id, ProductionLine.name))
        line_names = {str(row[0]): row[1] for row in line_result.all()}

        lines: List[PlanExecutionLineItem] = []
        total_target = Decimal("0")
        total_actual = Decimal("0")

        for row in rows:
            target = Decimal(str(row.target_quantity or 0))
            actual = Decimal(str(row.actual_quantity or 0))
            fulfillment = (
                (actual / target * 100).quantize(Decimal("0.01"))
                if target > 0
                else Decimal("0.00")
            )
            total_target += target
            total_actual += actual
            line_name = line_names.get(str(row.production_line), row.production_line)
            lines.append(
                PlanExecutionLineItem(
                    production_line=line_name,
                    target_quantity=target,
                    actual_quantity=actual,
                    fulfillment_pct=fulfillment,
                    orders_planned=int(row.orders_planned or 0),
                    orders_in_progress=int(row.orders_in_progress or 0),
                    orders_completed=int(row.orders_completed or 0),
                    orders_cancelled=int(row.orders_cancelled or 0),
                    total_snapshots=int(row.total_snapshots or 0),
                )
            )

        overall_fulfillment = (
            (total_actual / total_target * 100).quantize(Decimal("0.01"))
            if total_target > 0
            else Decimal("0.00")
        )

        logger.info(
            "plan_execution_calculated",
            date_from=str(date_from),
            date_to=str(date_to),
            line_count=len(lines),
        )

        return PlanExecutionResponse(
            period_from=date_from,
            period_to=date_to,
            lines=lines,
            total_target=total_target,
            total_actual=total_actual,
            overall_fulfillment_pct=overall_fulfillment,
        )

    async def get_downtime_ranking(
        self,
        date_from: date,
        date_to: date,
    ) -> DowntimeRankingResponse:
        """
        Return production lines ranked by total delay hours (Pareto order).

        Only considers completed orders with both planned_end and actual_end set.
        Delay is calculated in Python to avoid dialect-specific SQL interval operations.
        """
        query = (
            select(
                OrderSnapshot.production_line,
                OrderSnapshot.planned_end,
                OrderSnapshot.actual_end,
            )
            .where(
                OrderSnapshot.snapshot_date >= date_from,
                OrderSnapshot.snapshot_date <= date_to,
                OrderSnapshot.status == "completed",
                OrderSnapshot.actual_end.isnot(None),
                OrderSnapshot.planned_end.isnot(None),
            )
            .order_by(OrderSnapshot.production_line)
        )
        result = await self.db.execute(query)
        rows = result.all()

        # Build production line UUID -> name map
        from app.models.reference import ProductionLine
        line_result = await self.db.execute(select(ProductionLine.id, ProductionLine.name))
        line_names = {str(row[0]): row[1] for row in line_result.all()}

        # Aggregate delay stats per line in Python
        line_stats: Dict[Optional[str], Dict] = {}
        for row in rows:
            key = row.production_line
            if key and key in line_names:
                key = line_names[key]
            if key not in line_stats:
                line_stats[key] = {
                    "total_delay_hours": Decimal("0"),
                    "delayed_orders": 0,
                    "total_completed": 0,
                }
            line_stats[key]["total_completed"] += 1
            diff_seconds = (row.actual_end - row.planned_end).total_seconds()
            if diff_seconds > 0:
                delay_hours = Decimal(str(round(diff_seconds / 3600, 4)))
                line_stats[key]["total_delay_hours"] += delay_hours
                line_stats[key]["delayed_orders"] += 1

        # Build items, sorted worst-first
        items: List[DowntimeLineItem] = []
        for production_line, stats in line_stats.items():
            total_delay = stats["total_delay_hours"].quantize(Decimal("0.0001"))
            delayed = stats["delayed_orders"]
            total_comp = stats["total_completed"]
            avg_delay = (
                (total_delay / Decimal(str(delayed))).quantize(Decimal("0.0001"))
                if delayed > 0
                else Decimal("0.0000")
            )
            delay_pct = (
                (Decimal(str(delayed)) / Decimal(str(total_comp)) * 100).quantize(Decimal("0.01"))
                if total_comp > 0
                else Decimal("0.00")
            )
            items.append(
                DowntimeLineItem(
                    production_line=production_line,
                    total_delay_hours=total_delay,
                    delayed_orders=delayed,
                    avg_delay_hours=avg_delay,
                    total_completed=total_comp,
                    delay_pct=delay_pct,
                )
            )

        items.sort(key=lambda x: x.total_delay_hours, reverse=True)

        grand_delay = sum((i.total_delay_hours for i in items), Decimal("0"))
        grand_delayed_orders = sum(i.delayed_orders for i in items)

        logger.info(
            "downtime_ranking_calculated",
            date_from=str(date_from),
            date_to=str(date_to),
            line_count=len(items),
        )

        return DowntimeRankingResponse(
            period_from=date_from,
            period_to=date_to,
            lines=items,
            total_delay_hours=grand_delay,
            total_delayed_orders=grand_delayed_orders,
        )
