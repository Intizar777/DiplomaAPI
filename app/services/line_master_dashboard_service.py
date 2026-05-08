"""
Line Master Dashboard business logic service.
Provides shift-level production and quality summaries for line masters.
"""
from datetime import date
from decimal import Decimal
from typing import Dict, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProductionOutput, QualityResult
from app.schemas.line_master_dashboard import (
    ShiftItem,
    ShiftProgressResponse,
    ShiftComparisonPeriod,
    ShiftComparisonResponse,
    DefectItem,
    DefectSummaryResponse,
)
import structlog

logger = structlog.get_logger()


class LineMasterDashboardService:
    """
    Service for Line Master production and quality dashboards.
    All times are local shift times; no timezone conversion.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_shift_progress(self, production_date: date) -> ShiftProgressResponse:
        """
        Get production progress for all shifts on a given production date.
        Aggregates: lot count, total quantity, approved lots, defect count.
        """
        # Fetch all outputs for the date
        query = select(ProductionOutput).where(
            ProductionOutput.production_date == production_date
        ).order_by(ProductionOutput.shift)

        result = await self.db.execute(query)
        outputs = result.scalars().all()

        # Aggregate by shift
        shifts_dict: Dict[str, Dict] = {}
        for output in outputs:
            shift_key = output.shift or "unknown"
            if shift_key not in shifts_dict:
                shifts_dict[shift_key] = {
                    "shift": shift_key,
                    "lot_count": 0,
                    "total_quantity": Decimal("0"),
                    "approved_count": 0,
                    "defect_count": 0,
                }
            shifts_dict[shift_key]["lot_count"] += 1
            shifts_dict[shift_key]["total_quantity"] += output.quantity or Decimal("0")
            if output.quality_status and output.quality_status.lower() == "approved":
                shifts_dict[shift_key]["approved_count"] += 1

        # Count defects per shift (query quality_results by lot_number)
        quality_query = select(QualityResult).where(
            QualityResult.test_date == production_date
        )
        quality_result = await self.db.execute(quality_query)
        quality_results = quality_result.scalars().all()

        # Build map of lot_number -> defects
        defects_by_lot: Dict[str, bool] = {}
        for qr in quality_results:
            if qr.lot_number not in defects_by_lot:
                defects_by_lot[qr.lot_number] = False
            if not qr.in_spec:
                defects_by_lot[qr.lot_number] = True

        # Count defects per shift
        for output in outputs:
            if output.lot_number in defects_by_lot and defects_by_lot[output.lot_number]:
                shift_key = output.shift or "unknown"
                if shift_key in shifts_dict:
                    shifts_dict[shift_key]["defect_count"] += 1

        # Calculate defect rates
        shifts_list: List[ShiftItem] = []
        total_qty = Decimal("0")
        total_lots = 0

        for shift_data in shifts_dict.values():
            defect_rate = Decimal("0")
            if shift_data["lot_count"] > 0:
                defect_rate = (
                    Decimal(shift_data["defect_count"]) / Decimal(shift_data["lot_count"]) * 100
                )
                defect_rate = defect_rate.quantize(Decimal("0.01"))

            shifts_list.append(
                ShiftItem(
                    shift=shift_data["shift"],
                    lot_count=shift_data["lot_count"],
                    total_quantity=shift_data["total_quantity"].quantize(Decimal("0.01")),
                    approved_count=shift_data["approved_count"],
                    defect_count=shift_data["defect_count"],
                    defect_rate=defect_rate,
                )
            )
            total_qty += shift_data["total_quantity"]
            total_lots += shift_data["lot_count"]

        logger.info(
            "shift_progress_calculated",
            date=str(production_date),
            shift_count=len(shifts_list),
            total_lots=total_lots,
        )

        return ShiftProgressResponse(
            date=production_date,
            shifts=shifts_list,
            total_quantity=total_qty.quantize(Decimal("0.01")),
            total_lots=total_lots,
        )

    async def get_shift_comparison(
        self, from_date: date, to_date: date
    ) -> ShiftComparisonResponse:
        """
        Get production data for all shifts over a date range.
        Useful for comparing shift performance across days.
        """
        # Aggregate output by production_date and shift
        query = select(
            ProductionOutput.production_date,
            ProductionOutput.shift,
            func.count(ProductionOutput.id).label("lot_count"),
            func.sum(ProductionOutput.quantity).label("total_quantity"),
        ).where(
            ProductionOutput.production_date >= from_date,
            ProductionOutput.production_date <= to_date,
        ).group_by(
            ProductionOutput.production_date,
            ProductionOutput.shift,
        ).order_by(
            ProductionOutput.production_date,
            ProductionOutput.shift,
        )

        result = await self.db.execute(query)
        rows = result.all()

        # Count defects by date and shift
        quality_query = select(
            QualityResult.test_date,
            func.count(QualityResult.id).label("defect_count"),
        ).where(
            QualityResult.test_date >= from_date,
            QualityResult.test_date <= to_date,
            QualityResult.in_spec == False,
        ).group_by(QualityResult.test_date)

        quality_result = await self.db.execute(quality_query)
        quality_rows = quality_result.all()

        defect_map: Dict[str, int] = {}
        for qr in quality_rows:
            key = str(qr[0])  # test_date
            defect_map[key] = qr[1]

        # Build response items
        items: List[ShiftComparisonPeriod] = []
        for row in rows:
            date_key = str(row.production_date)
            defect_count = defect_map.get(date_key, 0)
            items.append(
                ShiftComparisonPeriod(
                    date=row.production_date,
                    shift=row.shift,
                    total_quantity=(row.total_quantity or Decimal("0")).quantize(
                        Decimal("0.01")
                    ),
                    lot_count=row.lot_count,
                    defect_count=defect_count,
                )
            )

        logger.info(
            "shift_comparison_calculated",
            from_date=str(from_date),
            to_date=str(to_date),
            item_count=len(items),
        )

        return ShiftComparisonResponse(
            period_from=from_date,
            period_to=to_date,
            shifts=items,
        )

    async def get_defect_summary(
        self, from_date: date, to_date: date
    ) -> DefectSummaryResponse:
        """
        Analyze quality defects by parameter over a date range.
        Shows which parameters fail most frequently.
        """
        # Fetch all quality results for the date range
        query = select(QualityResult).where(
            QualityResult.test_date >= from_date,
            QualityResult.test_date <= to_date,
        )

        result = await self.db.execute(query)
        quality_results = result.scalars().all()

        # Aggregate by parameter_name in Python
        param_stats: Dict[str, Dict] = {}
        total_defects = 0

        for qr in quality_results:
            param = qr.parameter_name or "unknown"
            if param not in param_stats:
                param_stats[param] = {
                    "total_tests": 0,
                    "failed_tests": 0,
                }
            param_stats[param]["total_tests"] += 1
            if not qr.in_spec:
                param_stats[param]["failed_tests"] += 1
                total_defects += 1

        # Build response items, sorted by failed_tests descending
        items: List[DefectItem] = []
        for param, stats in sorted(
            param_stats.items(),
            key=lambda x: x[1]["failed_tests"],
            reverse=True,
        ):
            failed = stats["failed_tests"]
            total = stats["total_tests"]
            fail_rate = (Decimal(failed) / Decimal(total) * 100).quantize(
                Decimal("0.01")
            )

            items.append(
                DefectItem(
                    parameter_name=param,
                    total_tests=total,
                    failed_tests=failed,
                    fail_rate=fail_rate,
                )
            )

        logger.info(
            "defect_summary_calculated",
            from_date=str(from_date),
            to_date=str(to_date),
            parameter_count=len(items),
            total_defects=total_defects,
        )

        return DefectSummaryResponse(
            period_from=from_date,
            period_to=to_date,
            total_defects=total_defects,
            items=items,
        )
