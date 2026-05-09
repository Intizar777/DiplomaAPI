"""
Quality Engineer Dashboard service.
"""
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func, case, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.quality import QualityResult
from app.models.reference import QualitySpec
from app.models.output import ProductionOutput
from app.schemas.qe_dashboard import (
    TrendDataPoint,
    ParameterTrendItem,
    ParameterTrendsResponse,
    DeviationItem,
    BatchAnalysisItem,
    BatchAnalysisResponse,
    ParetoItem,
    DefectParetoResponse,
)

logger = structlog.get_logger()


class QualityEngineerDashboardService:
    """Provides parameter-level quality analytics for Quality Engineers."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_parameter_trends(
        self,
        date_from: date,
        date_to: date,
    ) -> ParameterTrendsResponse:
        """
        Return daily parameter quality trends with spec bands.

        Single query GROUP BY parameter_name + test_date.
        MAX() for spec limits collapses correctly since each (param, day)
        maps to one spec row.
        """
        query = (
            select(
                QualityResult.parameter_name,
                QualityResult.test_date,
                func.avg(QualityResult.result_value).label("avg_value"),
                func.count(QualityResult.id).label("test_count"),
                func.sum(
                    case((QualityResult.in_spec == False, 1), else_=0)  # noqa: E712
                ).label("out_of_spec_count"),
                func.max(QualitySpec.lower_limit).label("lower_limit"),
                func.max(QualitySpec.upper_limit).label("upper_limit"),
            )
            .outerjoin(QualitySpec, QualitySpec.id == QualityResult.quality_spec_id)
            .where(
                QualityResult.test_date >= date_from,
                QualityResult.test_date <= date_to,
            )
            .group_by(QualityResult.parameter_name, QualityResult.test_date)
            .order_by(QualityResult.parameter_name, QualityResult.test_date)
        )
        result = await self.db.execute(query)
        rows = result.all()

        # Group rows by parameter_name
        param_points: Dict[str, List[TrendDataPoint]] = {}
        for row in rows:
            param = row.parameter_name
            test_count = int(row.test_count or 0)
            out_of_spec = int(row.out_of_spec_count or 0)
            out_of_spec_pct = (
                (Decimal(str(out_of_spec)) / Decimal(str(test_count)) * 100).quantize(Decimal("0.01"))
                if test_count > 0
                else Decimal("0.00")
            )
            point = TrendDataPoint(
                test_date=row.test_date,
                avg_value=Decimal(str(row.avg_value or 0)).quantize(Decimal("0.0001")),
                test_count=test_count,
                out_of_spec_count=out_of_spec,
                out_of_spec_pct=out_of_spec_pct,
                lower_limit=Decimal(str(row.lower_limit)) if row.lower_limit is not None else None,
                upper_limit=Decimal(str(row.upper_limit)) if row.upper_limit is not None else None,
            )
            if param not in param_points:
                param_points[param] = []
            param_points[param].append(point)

        # Build ParameterTrendItem per parameter
        parameters: List[ParameterTrendItem] = []
        for param_name, points in param_points.items():
            total_tests = sum(p.test_count for p in points)
            total_oos = sum(p.out_of_spec_count for p in points)
            overall_pct = (
                (Decimal(str(total_oos)) / Decimal(str(total_tests)) * 100).quantize(Decimal("0.01"))
                if total_tests > 0
                else Decimal("0.00")
            )
            parameters.append(
                ParameterTrendItem(
                    parameter_name=param_name,
                    total_tests=total_tests,
                    total_out_of_spec=total_oos,
                    overall_out_of_spec_pct=overall_pct,
                    trend=points,
                )
            )

        logger.info(
            "parameter_trends_calculated",
            date_from=str(date_from),
            date_to=str(date_to),
            parameter_count=len(parameters),
        )

        return ParameterTrendsResponse(
            period_from=date_from,
            period_to=date_to,
            parameters=parameters,
        )

    async def get_batch_analysis(
        self,
        date_from: date,
        date_to: date,
    ) -> BatchAnalysisResponse:
        """
        Return lots with deviations, with per-parameter deviation details.

        Two-pass approach to avoid cross-product with multi-snapshot ProductionOutput:
        Pass 1: failing QualityResult rows + spec limits.
        Pass 2: production metadata for those lots only.
        """
        # Pass 1 — fetch failing quality rows
        quality_query = (
            select(
                QualityResult.lot_number,
                QualityResult.parameter_name,
                QualityResult.result_value,
                QualitySpec.lower_limit,
                QualitySpec.upper_limit,
            )
            .outerjoin(QualitySpec, QualitySpec.id == QualityResult.quality_spec_id)
            .where(
                QualityResult.test_date >= date_from,
                QualityResult.test_date <= date_to,
                QualityResult.in_spec == False,  # noqa: E712
            )
            .order_by(QualityResult.lot_number)
        )
        quality_result = await self.db.execute(quality_query)
        quality_rows = quality_result.all()

        # Collect deviations per lot
        lot_to_deviations: Dict[str, List[DeviationItem]] = {}
        for row in quality_rows:
            lot = row.lot_number
            result_val = Decimal(str(row.result_value or 0))
            lower = Decimal(str(row.lower_limit)) if row.lower_limit is not None else None
            upper = Decimal(str(row.upper_limit)) if row.upper_limit is not None else None

            if lower is not None and upper is not None:
                if result_val > upper:
                    magnitude = (result_val - upper).quantize(Decimal("0.0001"))
                else:
                    magnitude = (lower - result_val).quantize(Decimal("0.0001"))
            else:
                magnitude = Decimal("0.0000")

            deviation = DeviationItem(
                parameter_name=row.parameter_name,
                result_value=result_val,
                lower_limit=lower,
                upper_limit=upper,
                deviation_magnitude=magnitude,
            )
            if lot not in lot_to_deviations:
                lot_to_deviations[lot] = []
            lot_to_deviations[lot].append(deviation)

        failing_lot_numbers = set(lot_to_deviations.keys())

        # Pass 2 — production metadata
        lot_metadata: Dict[str, dict] = {}
        if failing_lot_numbers:
            output_query = (
                select(
                    ProductionOutput.lot_number,
                    ProductionOutput.product_name,
                    ProductionOutput.production_date,
                    ProductionOutput.shift,
                )
                .where(ProductionOutput.lot_number.in_(list(failing_lot_numbers)))
                .order_by(ProductionOutput.production_date.desc())
            )
            output_result = await self.db.execute(output_query)
            output_rows = output_result.all()
            # First-seen-wins after DESC sort = latest snapshot
            for row in output_rows:
                if row.lot_number not in lot_metadata:
                    lot_metadata[row.lot_number] = {
                        "product_name": row.product_name,
                        "production_date": row.production_date,
                        "shift": row.shift,
                    }

        # Assembly
        lots: List[BatchAnalysisItem] = []
        for lot_number, deviations in lot_to_deviations.items():
            meta = lot_metadata.get(lot_number, {})
            lots.append(
                BatchAnalysisItem(
                    lot_number=lot_number,
                    product_name=meta.get("product_name"),
                    production_date=meta.get("production_date"),
                    shift=meta.get("shift"),
                    fail_count=len(deviations),
                    deviations=deviations,
                )
            )

        # Sort by production_date ascending, None last
        lots.sort(key=lambda x: (x.production_date is None, x.production_date))

        logger.info(
            "batch_analysis_calculated",
            date_from=str(date_from),
            date_to=str(date_to),
            lot_count=len(lots),
        )

        return BatchAnalysisResponse(
            period_from=date_from,
            period_to=date_to,
            lot_count=len(lots),
            lots=lots,
        )

    async def get_defect_pareto(
        self,
        date_from: date,
        date_to: date,
        product_id: Optional[UUID] = None,
    ) -> DefectParetoResponse:
        """
        Return parameters ranked by defect count (Pareto chart) with cumulative %.

        Optional product_id filter. Cumulative % calculated in Python.
        """
        conditions = [
            QualityResult.test_date >= date_from,
            QualityResult.test_date <= date_to,
        ]
        if product_id is not None:
            conditions.append(QualityResult.product_id == product_id)

        query = (
            select(
                QualityResult.parameter_name,
                func.count(QualityResult.id).label("total_tests"),
                func.sum(
                    case((QualityResult.in_spec == False, 1), else_=0)  # noqa: E712
                ).label("defect_count"),
            )
            .where(*conditions)
            .group_by(QualityResult.parameter_name)
            .order_by(func.sum(case((QualityResult.in_spec == False, 1), else_=0)).desc())  # noqa: E712
        )
        result = await self.db.execute(query)
        rows = result.all()

        grand_total = sum(int(row.defect_count or 0) for row in rows)

        running_sum = 0
        parameters: List[ParetoItem] = []
        for row in rows:
            total_tests = int(row.total_tests or 0)
            defect_count = int(row.defect_count or 0)
            running_sum += defect_count
            defect_pct = (
                (Decimal(str(defect_count)) / Decimal(str(total_tests)) * 100).quantize(Decimal("0.01"))
                if total_tests > 0
                else Decimal("0.00")
            )
            cumulative_pct = (
                (Decimal(str(running_sum)) / Decimal(str(grand_total)) * 100).quantize(Decimal("0.01"))
                if grand_total > 0
                else Decimal("0.00")
            )
            parameters.append(
                ParetoItem(
                    parameter_name=row.parameter_name,
                    defect_count=defect_count,
                    total_tests=total_tests,
                    defect_pct=defect_pct,
                    cumulative_pct=cumulative_pct,
                )
            )

        logger.info(
            "defect_pareto_calculated",
            date_from=str(date_from),
            date_to=str(date_to),
            product_id=str(product_id) if product_id else None,
            total_defects=grand_total,
        )

        return DefectParetoResponse(
            period_from=date_from,
            period_to=date_to,
            product_id=product_id,
            total_defects=grand_total,
            parameters=parameters,
        )
