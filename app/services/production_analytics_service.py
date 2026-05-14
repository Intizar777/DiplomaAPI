"""
Production analytics service for enriched KPI, OTIF, breakdown, and margin calculations.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Literal, List
from uuid import UUID as UUIDType

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AggregatedKPI, OrderSnapshot, QualityResult, SaleRecord, ProductionLine, BatchInput, ProductionOutput, DowntimeEvent
import structlog

logger = structlog.get_logger()


class ProductionAnalyticsService:
    """Service for production analytics (enriched KPI, OTIF, breakdown, margin)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_kpi(
        self,
        from_date: date,
        to_date: date,
        production_line_id: Optional[str] = None,
        granularity: Literal["day", "week", "month"] = "day",
        compare_with_previous: bool = False
    ) -> dict:
        """Get enriched KPI with targets, trends, and optional comparison."""
        # Fetch aggregated KPI for period
        kpi_query = select(AggregatedKPI).where(
            AggregatedKPI.period_from >= from_date,
            AggregatedKPI.period_to <= to_date,
        )

        if production_line_id:
            kpi_query = kpi_query.where(AggregatedKPI.product_line_id == production_line_id)
        else:
            # Use aggregated across all lines (production_line is NULL)
            kpi_query = kpi_query.where(AggregatedKPI.product_line_id == None)

        result = await self.db.execute(kpi_query)
        kpi_records = result.scalars().all()

        if not kpi_records:
            logger.warning("kpi_no_data", from_date=from_date, to_date=to_date)
            return self._empty_kpi_response()

        # Aggregate metrics for the period
        latest = kpi_records[-1] if kpi_records else None
        total_output = sum(r.total_output for r in kpi_records)
        avg_defect_rate = (sum(r.defect_rate for r in kpi_records) / len(kpi_records)) if kpi_records else Decimal("0")
        total_orders = sum(r.total_orders for r in kpi_records)
        completed_orders = sum(r.completed_orders for r in kpi_records)
        oee_estimate = (sum(r.oee_estimate for r in kpi_records) / len(kpi_records)) if kpi_records and kpi_records[0].oee_estimate else Decimal("0.80")

        # Get OTIF data
        otif_data = await self.get_otif(from_date, to_date, production_line_id)
        otif_rate = otif_data["otif_rate"]

        # KPI targets (hardcoded, can be made configurable)
        targets = {
            "oee_estimate": {
                "target": Decimal("0.85"),
                "min": Decimal("0.75"),
                "max": Decimal("1.0"),
                "status": self._get_status(oee_estimate, Decimal("0.85"), Decimal("0.75"), Decimal("1.0")),
            },
            "defect_rate": {
                "target": Decimal("0.015"),
                "min": Decimal("0.0"),
                "max": Decimal("0.015"),
                "status": self._get_status(avg_defect_rate, Decimal("0.015"), Decimal("0.0"), Decimal("0.015")),
            },
            "otif_rate": {
                "target": Decimal("0.95"),
                "min": Decimal("0.9"),
                "max": Decimal("1.0"),
                "status": self._get_status(otif_rate, Decimal("0.95"), Decimal("0.9"), Decimal("1.0")),
            },
        }

        # Build trend data (group by day, week, or month based on granularity)
        trend_points = []
        for kpi_rec in kpi_records:
            if granularity == "day":
                period_label = kpi_rec.period_from.isoformat()
            elif granularity == "week":
                period_label = str(kpi_rec.period_from.isocalendar()[1])
            else:
                period_label = kpi_rec.period_from.strftime("%Y-%m")

            trend_points.append({
                "period": period_label,
                "total_output": kpi_rec.total_output,
                "defect_rate": kpi_rec.defect_rate,
                "oee_estimate": kpi_rec.oee_estimate or Decimal("0.80"),
            })

        # Compute availability and performance (derived from OEE = Availability × Performance × Quality)
        # For simplicity: availability = 0.95, performance = 0.92, quality = oee / (0.95 * 0.92)
        availability = Decimal("0.95")
        performance = Decimal("0.92")

        # Calculate change percent if requested
        change_percent = {}
        if compare_with_previous:
            prev_from = from_date - (to_date - from_date)
            prev_to = from_date - timedelta(days=1)

            prev_query = select(AggregatedKPI).where(
                AggregatedKPI.period_from >= prev_from,
                AggregatedKPI.period_to <= prev_to,
            )
            if production_line_id:
                prev_query = prev_query.where(AggregatedKPI.product_line_id == production_line_id)
            else:
                prev_query = prev_query.where(AggregatedKPI.product_line_id == None)

            prev_result = await self.db.execute(prev_query)
            prev_records = prev_result.scalars().all()

            if prev_records:
                prev_output = sum(r.total_output for r in prev_records)
                prev_oee = (sum(r.oee_estimate for r in prev_records) / len(prev_records)) if prev_records[0].oee_estimate else Decimal("0.80")

                change_percent = {
                    "total_output": float((total_output - prev_output) / prev_output * 100) if prev_output > 0 else 0,
                    "oee_estimate": float((oee_estimate - prev_oee) / prev_oee * 100) if prev_oee > 0 else 0,
                }

        # Line throughput (simplified: total_output / number of days)
        days = (to_date - from_date).days + 1
        line_throughput = total_output / days if days > 0 else Decimal("0")

        return {
            "total_output": total_output,
            "defect_rate": avg_defect_rate,
            "completed_orders": completed_orders,
            "total_orders": total_orders,
            "availability": availability,
            "performance": performance,
            "oee_estimate": oee_estimate,
            "line_throughput": line_throughput,
            "targets": targets,
            "trend": trend_points,
            "change_percent": change_percent if change_percent else None,
        }

    async def get_otif(self, from_date: date, to_date: date, production_line_id: Optional[str] = None) -> dict:
        """Get OTIF (On-Time In-Full) metrics."""
        query = select(OrderSnapshot).where(
            OrderSnapshot.actual_start >= datetime.combine(from_date, datetime.min.time()),
            OrderSnapshot.actual_end <= datetime.combine(to_date, datetime.max.time()),
        )

        if production_line_id:
            query = query.where(OrderSnapshot.production_line == production_line_id)

        result = await self.db.execute(query)
        orders = result.scalars().all()

        on_time = sum(1 for o in orders if o.actual_end and o.planned_end and o.actual_end <= o.planned_end)
        in_full = sum(1 for o in orders if o.status == "completed")
        otif = sum(1 for o in orders if o.status == "completed" and o.actual_end and o.planned_end and o.actual_end <= o.planned_end)

        total = len(orders)
        otif_rate = (otif / total) if total > 0 else Decimal("0")

        return {
            "otif_rate": otif_rate,
            "on_time_orders": on_time,
            "in_full_quantity_orders": in_full,
            "otif_orders": otif,
            "total_orders": total,
        }

    async def get_kpi_breakdown(
        self,
        from_date: date,
        to_date: date,
        group_by: Literal["productionLine", "product", "division"],
        metric: Literal["oeeEstimate", "defectRate", "lineThroughput", "otifRate"] = "oeeEstimate",
        offset: int = 0,
        limit: int = 20
    ) -> dict:
        """Get KPI breakdown (drill-down) by group."""
        if group_by == "productionLine":
            # Group by production_line from aggregated_kpi
            query = select(
                AggregatedKPI.product_line_id.label("group_key"),
                func.avg(AggregatedKPI.oee_estimate).label("oee_estimate"),
                func.avg(AggregatedKPI.defect_rate).label("defect_rate"),
                func.sum(AggregatedKPI.total_output).label("total_output"),
            ).where(
                AggregatedKPI.period_from >= from_date,
                AggregatedKPI.period_to <= to_date,
                AggregatedKPI.product_line_id != None,
            ).group_by(AggregatedKPI.product_line_id)

            result = await self.db.execute(query)
            rows = result.all()

            items = []
            for row in rows:
                if metric == "oeeEstimate":
                    value = row.oee_estimate or Decimal("0.80")
                    target = Decimal("0.85")
                elif metric == "defectRate":
                    value = row.defect_rate
                    target = Decimal("0.015")
                elif metric == "lineThroughput":
                    days = (to_date - from_date).days + 1
                    value = (row.total_output / days) if days > 0 else Decimal("0")
                    target = Decimal("150")
                else:  # otifRate
                    value = Decimal("0.95")
                    target = Decimal("0.95")

                items.append({
                    "group_key": row.group_key or "unknown",
                    "value": value,
                    "target": target,
                    "status": self._get_status(value, target, target - Decimal("0.1"), target + Decimal("0.1")),
                    "deviation": value - target,
                })

        elif group_by == "division":
            # Join with production_lines to get division
            query = select(
                ProductionLine.division.label("group_key"),
                func.avg(AggregatedKPI.oee_estimate).label("oee_estimate"),
            ).join(
                ProductionLine, AggregatedKPI.product_line_id == ProductionLine.code
            ).where(
                AggregatedKPI.period_from >= from_date,
                AggregatedKPI.period_to <= to_date,
            ).group_by(ProductionLine.division)

            result = await self.db.execute(query)
            rows = result.all()

            items = [
                {
                    "group_key": row.group_key or "unknown",
                    "value": row.oee_estimate or Decimal("0.80"),
                    "target": Decimal("0.85"),
                    "status": self._get_status(row.oee_estimate or Decimal("0.80"), Decimal("0.85"), Decimal("0.75"), Decimal("1.0")),
                    "deviation": (row.oee_estimate or Decimal("0.80")) - Decimal("0.85"),
                }
                for row in rows
            ]

        else:  # product
            items = []

        # Sort by value descending, paginate
        items_sorted = sorted(items, key=lambda x: x["value"], reverse=True)
        items_paginated = items_sorted[offset:offset + limit]

        return {
            "items": items_paginated,
            "total": len(items),
        }

    async def get_sales_margin(
        self,
        from_date: date,
        to_date: date,
        product_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 20
    ) -> dict:
        """Get sales margin by product (cost from Gateway API)."""
        query = select(
            SaleRecord.product_id,
            SaleRecord.product_name,
            func.sum(SaleRecord.quantity).label("total_quantity"),
            func.sum(SaleRecord.amount).label("total_revenue"),
            func.sum(SaleRecord.cost).label("total_cost"),
        ).where(
            SaleRecord.sale_date >= from_date,
            SaleRecord.sale_date <= to_date,
        )

        if product_id:
            query = query.where(SaleRecord.product_id == UUIDType(product_id))

        query = query.group_by(SaleRecord.product_id, SaleRecord.product_name)

        result = await self.db.execute(query)
        rows = result.all()

        # Calculate margins (cost from Gateway API)
        margins = []
        total_revenue = Decimal("0")
        total_cost = Decimal("0")
        total_margin = Decimal("0")

        for row in rows:
            revenue = row.total_revenue or Decimal("0")
            cost = row.total_cost or Decimal("0")
            margin = revenue - cost
            margin_percent = (margin / revenue * 100) if revenue > 0 else Decimal("0")
            margin_per_unit = (margin / row.total_quantity) if row.total_quantity > 0 else Decimal("0")

            margins.append({
                "product_id": str(row.product_id),
                "product_code": str(row.product_id)[:6] if row.product_id else "unknown",
                "product_name": row.product_name or "unknown",
                "total_quantity": row.total_quantity,
                "total_revenue": revenue,
                "total_cost": cost,
                "total_margin": margin,
                "margin_percent": margin_percent,
                "margin_per_unit": margin_per_unit,
            })

            total_revenue += revenue
            total_cost += cost
            total_margin += margin

        # Paginate
        margins_paginated = margins[offset:offset + limit]

        avg_margin_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else Decimal("0")

        return {
            "margins": margins_paginated,
            "total": len(margins),
            "aggregated": {
                "total_revenue": total_revenue,
                "total_cost": total_cost,
                "total_margin": total_margin,
                "avg_margin_percent": avg_margin_percent,
            },
        }

    async def get_line_productivity(
        self,
        from_date: date,
        to_date: date,
        production_line_id: Optional[str] = None,
    ) -> dict:
        """Get line productivity in tonnes per hour."""
        logger.info("get_line_productivity", from_date=from_date, to_date=to_date)

        query = select(
            AggregatedKPI.product_line_id,
            func.sum(AggregatedKPI.total_output).label("total_output"),
        ).where(
            and_(
                AggregatedKPI.period_from >= from_date,
                AggregatedKPI.period_to <= to_date,
                AggregatedKPI.product_line_id != None,
            )
        ).group_by(AggregatedKPI.product_line_id)

        if production_line_id:
            query = query.where(AggregatedKPI.product_line_id == production_line_id)

        result = await self.db.execute(query)
        rows = result.all()

        days = (to_date - from_date).days + 1
        items = []

        for row in rows:
            total_output = row.total_output or Decimal("0")
            # Assume 16 hours per day (can be fetched from LineCapacityPlan)
            total_hours = Decimal(16) * days
            productivity = (total_output / total_hours) if total_hours > 0 else Decimal("0")
            target = Decimal("2.5")  # tonnes/hour target

            items.append({
                "product_line_id": row.production_line or "unknown",
                "productivity": productivity,
                "total_output": total_output,
                "days": days,
                "target": target,
                "status": self._get_status(productivity, target, target - Decimal("0.5"), target + Decimal("1.0")),
                "deviation": productivity - target,
            })

        return {
            "items": items,
            "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
            "unit": "tonnes/hour",
        }

    async def get_scrap_percentage(
        self,
        from_date: date,
        to_date: date,
        product_id: Optional[str] = None,
    ) -> dict:
        """Get scrap percentage (quality defects)."""
        logger.info("get_scrap_percentage", from_date=from_date, to_date=to_date)

        # Count total quality tests
        total_query = select(func.count(QualityResult.id)).where(
            and_(
                QualityResult.test_date >= from_date,
                QualityResult.test_date <= to_date,
            )
        )

        if product_id:
            total_query = total_query.where(QualityResult.product_id == product_id)

        total_result = await self.db.execute(total_query)
        total_tests = total_result.scalar() or 0

        # Count rejected tests (decision != 'accepted' and != 'approved')
        rejected_query = select(func.count(QualityResult.id)).where(
            and_(
                QualityResult.test_date >= from_date,
                QualityResult.test_date <= to_date,
                QualityResult.decision.notin_(["accepted", "approved"]),
            )
        )

        if product_id:
            rejected_query = rejected_query.where(QualityResult.product_id == product_id)

        rejected_result = await self.db.execute(rejected_query)
        rejected_tests = rejected_result.scalar() or 0

        scrap_percent = (Decimal(rejected_tests) / Decimal(total_tests) * 100) if total_tests > 0 else Decimal("0")
        target = Decimal("1.5")

        return {
            "scrap_percentage": scrap_percent,
            "rejected_tests": rejected_tests,
            "total_tests": total_tests,
            "target": target,
            "status": self._get_status(scrap_percent, target, Decimal("0"), target + Decimal("1.0")),
            "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
        }

    def _get_status(self, value: Decimal, target: Decimal, min_val: Decimal, max_val: Decimal) -> str:
        """Determine status based on target range."""
        if value >= target:
            return "ok"
        elif value >= min_val:
            return "warning"
        else:
            return "critical"

    def _empty_kpi_response(self) -> dict:
        """Return empty KPI response structure."""
        return {
            "total_output": Decimal("0"),
            "defect_rate": Decimal("0"),
            "completed_orders": 0,
            "total_orders": 0,
            "availability": Decimal("0"),
            "performance": Decimal("0"),
            "oee_estimate": Decimal("0"),
            "line_throughput": Decimal("0"),
            "targets": {},
            "trend": [],
            "change_percent": None,
        }
