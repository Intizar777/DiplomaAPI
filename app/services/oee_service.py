"""
OEE (Overall Equipment Effectiveness) calculation service.
OEE = Availability × Performance × Quality / 10000
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DowntimeEvent,
    ProductionOutput,
    QualityResult,
    LineCapacityPlan,
    ProductionLine,
)
from app.schemas.oee import (
    OEEComponentResponse,
    OEELineResponse,
    OEESummaryResponse,
    LineCapacityPlanResponse,
)

logger = structlog.get_logger()


class OEEService:
    """Service for calculating OEE metrics."""

    async def calculate_oee_summary(
        self,
        session: AsyncSession,
        period_from: date,
        period_to: date,
        production_line_id: Optional[str] = None,
    ) -> OEESummaryResponse:
        """
        Calculate OEE summary for a period, optionally filtered by production line.
        """
        logger.info(
            "oee_calculate_summary_start",
            period_from=period_from,
            period_to=period_to,
            line_id=production_line_id,
        )

        # Fetch all production lines (or specific line)
        query = select(ProductionLine).filter(ProductionLine.is_active == True)
        if production_line_id:
            query = query.filter(ProductionLine.id == production_line_id)

        result = await session.execute(query)
        lines = result.scalars().all()

        oee_lines = []
        for line in lines:
            try:
                line_oee = await self.calculate_oee_for_line(
                    session, line.id, period_from, period_to
                )
                oee_lines.append(line_oee)
            except Exception as e:
                logger.warning(
                    "oee_calculate_line_failed",
                    line_id=line.id,
                    error=str(e),
                )

        # Summary statistics
        total_oee = Decimal(0)
        lines_above_target = 0
        lines_below_target = 0

        if oee_lines:
            total_oee = sum(line.oee for line in oee_lines) / len(oee_lines)
            for line in oee_lines:
                if line.oee >= line.target_oee:
                    lines_above_target += 1
                else:
                    lines_below_target += 1

        response = OEESummaryResponse(
            summary_date=date.today(),
            lines=oee_lines,
            total_oee=total_oee,
            lines_above_target=lines_above_target,
            lines_below_target=lines_below_target,
            period_from=period_from,
            period_to=period_to,
        )

        logger.info(
            "oee_calculate_summary_complete",
            lines_count=len(oee_lines),
            total_oee=float(total_oee),
        )

        return response

    async def calculate_oee_for_line(
        self,
        session: AsyncSession,
        production_line_id: str,
        period_from: date,
        period_to: date,
    ) -> OEELineResponse:
        """
        Calculate OEE for a specific production line over a period.
        OEE = Availability × Performance × Quality / 10000
        """
        # Get line info
        line = await session.get(ProductionLine, production_line_id)
        if not line:
            raise ValueError(f"Production line {production_line_id} not found")

        # Get line capacity plan (if exists)
        capacity_plan = await self._get_active_capacity_plan(
            session, production_line_id, period_from
        )

        # Calculate components
        availability = await self._calculate_availability(
            session, production_line_id, period_from, period_to, capacity_plan
        )
        performance = await self._calculate_performance(
            session, production_line_id, period_from, period_to, capacity_plan
        )
        quality = await self._calculate_quality(
            session, production_line_id, period_from, period_to
        )

        # Calculate OEE
        oee_value = (availability.value * performance.value * quality.value) / Decimal("10000")

        target_oee = capacity_plan.target_oee_percent if capacity_plan else Decimal("85")

        return OEELineResponse(
            production_line_id=str(production_line_id),
            production_line_name=line.name,
            availability=availability,
            performance=performance,
            quality=quality,
            oee=oee_value,
            target_oee=target_oee,
            period_from=period_from,
            period_to=period_to,
        )

    async def _calculate_availability(
        self,
        session: AsyncSession,
        production_line_id: str,
        period_from: date,
        period_to: date,
        capacity_plan: Optional[LineCapacityPlan],
    ) -> OEEComponentResponse:
        """
        Availability = (Planned Time - Downtime) / Planned Time × 100
        """
        # Planned time in minutes
        days_in_period = (period_to - period_from).days + 1
        planned_hours = (capacity_plan.planned_hours_per_day if capacity_plan else 16) * days_in_period
        planned_minutes = planned_hours * 60

        # Sum downtime in minutes for this line during period
        downtime_query = select(func.sum(DowntimeEvent.duration_minutes)).filter(
            and_(
                DowntimeEvent.production_line_id == production_line_id,
                DowntimeEvent.started_at >= datetime.combine(period_from, datetime.min.time()),
                DowntimeEvent.started_at <= datetime.combine(period_to, datetime.max.time()),
            )
        )
        result = await session.execute(downtime_query)
        total_downtime_minutes = result.scalar() or 0

        # Availability percentage
        availability_value = (
            ((planned_minutes - total_downtime_minutes) / planned_minutes * 100)
            if planned_minutes > 0
            else Decimal("0")
        )
        availability_value = Decimal(str(min(100, max(0, float(availability_value)))))

        target = Decimal("90")
        status = self._get_status(availability_value, target)

        return OEEComponentResponse(
            component="availability",
            value=availability_value,
            target=target,
            status=status,
        )

    async def _calculate_performance(
        self,
        session: AsyncSession,
        production_line_id: str,
        period_from: date,
        period_to: date,
        capacity_plan: Optional[LineCapacityPlan],
    ) -> OEEComponentResponse:
        """
        Performance = (Actual Output / Planned Output) × 100
        For simplicity, we use average daily output vs expected output per operating hour.
        """
        # Get actual output for period
        output_query = select(func.sum(ProductionOutput.quantity)).filter(
            and_(
                ProductionOutput.production_date >= period_from,
                ProductionOutput.production_date <= period_to,
            )
        )
        result = await session.execute(output_query)
        actual_output = float(result.scalar() or 0)

        # Estimate planned output (assume 1 unit per hour as default)
        planned_hours = (capacity_plan.planned_hours_per_day if capacity_plan else 16) * (
            (period_to - period_from).days + 1
        )
        planned_output = float(planned_hours)

        # Performance percentage
        performance_value = (
            (actual_output / planned_output * 100) if planned_output > 0 else Decimal("0")
        )
        performance_value = Decimal(str(min(100, max(0, float(performance_value)))))

        target = Decimal("95")
        status = self._get_status(performance_value, target)

        return OEEComponentResponse(
            component="performance",
            value=performance_value,
            target=target,
            status=status,
        )

    async def _calculate_quality(
        self,
        session: AsyncSession,
        production_line_id: str,
        period_from: date,
        period_to: date,
    ) -> OEEComponentResponse:
        """
        Quality = (Accepted Lots / Total Lots) × 100
        """
        # Count total quality results for lots produced in period
        quality_query = select(func.count(QualityResult.id)).filter(
            and_(
                QualityResult.test_date >= period_from,
                QualityResult.test_date <= period_to,
            )
        )
        result = await session.execute(quality_query)
        total_tests = result.scalar() or 0

        # Count accepted quality results (decision = 'accepted')
        accepted_query = select(func.count(QualityResult.id)).filter(
            and_(
                QualityResult.test_date >= period_from,
                QualityResult.test_date <= period_to,
                QualityResult.decision == "accepted",
            )
        )
        result = await session.execute(accepted_query)
        accepted_tests = result.scalar() or 0

        # Quality percentage
        quality_value = (
            (accepted_tests / total_tests * 100) if total_tests > 0 else Decimal("100")
        )
        quality_value = Decimal(str(min(100, max(0, float(quality_value)))))

        target = Decimal("99")
        status = self._get_status(quality_value, target)

        return OEEComponentResponse(
            component="quality",
            value=quality_value,
            target=target,
            status=status,
        )

    async def _get_active_capacity_plan(
        self,
        session: AsyncSession,
        production_line_id: str,
        period_date: date,
    ) -> Optional[LineCapacityPlan]:
        """Get active capacity plan for a line on a specific date."""
        query = select(LineCapacityPlan).filter(
            and_(
                LineCapacityPlan.production_line_id == production_line_id,
                LineCapacityPlan.period_from <= period_date,
                (
                    (LineCapacityPlan.period_to.is_(None))
                    | (LineCapacityPlan.period_to >= period_date)
                ),
            )
        )
        result = await session.execute(query)
        return result.scalars().first()

    @staticmethod
    def _get_status(value: Decimal, target: Decimal) -> str:
        """
        Determine status based on value vs target.
        good: >= target
        warning: target-10% to target
        poor: < target-10%
        """
        if value >= target:
            return "good"
        elif value >= target - Decimal("10"):
            return "warning"
        else:
            return "poor"

    async def set_capacity_plan(
        self,
        session: AsyncSession,
        production_line_id: str,
        planned_hours_per_day: int,
        target_oee_percent: Decimal,
        period_from: date,
        period_to: Optional[date] = None,
    ) -> LineCapacityPlanResponse:
        """Create or update capacity plan for a production line."""
        import uuid

        plan = LineCapacityPlan(
            id=uuid.uuid4(),
            production_line_id=production_line_id,
            planned_hours_per_day=planned_hours_per_day,
            target_oee_percent=target_oee_percent,
            period_from=period_from,
            period_to=period_to,
        )
        session.add(plan)
        await session.commit()
        await session.refresh(plan)

        logger.info(
            "oee_capacity_plan_created",
            line_id=production_line_id,
            hours=planned_hours_per_day,
            target_oee=float(target_oee_percent),
        )

        return LineCapacityPlanResponse(
            id=str(plan.id),
            production_line_id=str(plan.production_line_id),
            planned_hours_per_day=plan.planned_hours_per_day,
            target_oee_percent=plan.target_oee_percent,
            period_from=plan.period_from,
            period_to=plan.period_to,
            created_at=plan.created_at.isoformat() if plan.created_at else "",
            updated_at=plan.updated_at.isoformat() if plan.updated_at else "",
        )
