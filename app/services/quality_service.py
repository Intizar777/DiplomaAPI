"""
Quality business logic service.
"""
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import QualityResult, QualitySpec, Product
from app.models.output import ProductionOutput
from app.models.orders import OrderSnapshot
from app.schemas import QualitySummaryResponse, DefectTrendsResponse, QualityLotsResponse, LotDeviationItem, LotDeviationsResponse
from app.schemas.qe_dashboard import (
    TrendDataPoint,
    ParameterTrendItem,
    ParameterTrendsResponse,
    ParetoItem,
    DefectParetoResponse,
)
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
import structlog

logger = structlog.get_logger()


class QualityService:
    """Service for quality business logic."""

    def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
        self.db = db
        self.gateway = gateway

    async def _sync_quality_spec(self, product_id: UUID, parameter_name: str, spec_data: dict) -> Optional[UUID]:
        """Sync a quality spec and return its ID."""
        if not spec_data or not product_id or not parameter_name:
            return None

        spec_id_raw = spec_data.get("id")
        try:
            spec_id = UUID(spec_id_raw) if isinstance(spec_id_raw, str) else spec_id_raw
        except (ValueError, AttributeError, TypeError):
            spec_id = None
        if spec_id is None:
            spec_id = uuid4()

        # Try to find existing by (product_id, parameter_name) unique constraint
        existing = await self.db.execute(
            select(QualitySpec).where(
                QualitySpec.product_id == product_id,
                QualitySpec.parameter_name == parameter_name
            )
        )
        spec = existing.scalar_one_or_none()

        if spec:
            spec.lower_limit = Decimal(str(spec_data.get("lowerLimit", spec.lower_limit)))
            spec.upper_limit = Decimal(str(spec_data.get("upperLimit", spec.upper_limit)))
            spec.is_active = spec_data.get("isActive", spec.is_active)
        else:
            spec = QualitySpec(
                id=spec_id,
                product_id=product_id,
                parameter_name=parameter_name,
                lower_limit=Decimal(str(spec_data.get("lowerLimit", 0))),
                upper_limit=Decimal(str(spec_data.get("upperLimit", 100))),
                is_active=spec_data.get("isActive", True),
            )
            self.db.add(spec)

        return spec.id

    async def get_quality_summary(
        self,
        from_date: date,
        to_date: date,
        product_id: Optional[str] = None
    ) -> QualitySummaryResponse:
        """Get quality summary."""
        query = select(QualityResult).where(
            QualityResult.test_date >= from_date,
            QualityResult.test_date <= to_date
        )
        
        if product_id:
            query = query.where(QualityResult.product_id == product_id)
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        # Calculate statistics
        total_tests = len(records)
        approved = sum(1 for r in records if r.decision == "approved")
        rejected = sum(1 for r in records if r.decision == "rejected")
        pending = sum(1 for r in records if r.decision == "pending")
        
        in_spec = sum(1 for r in records if r.in_spec)
        avg_quality = Decimal("0")
        if total_tests > 0:
            avg_quality = Decimal(in_spec / total_tests * 100).quantize(Decimal("0.1"))
        
        defect_rate = Decimal("0")
        if total_tests > 0:
            defect_rate = Decimal(rejected / total_tests * 100).quantize(Decimal("0.1"))
        
        # Stats by parameter
        by_param: Dict[str, Dict] = {}
        for record in records:
            param = record.parameter_name
            if param not in by_param:
                by_param[param] = {"total": 0, "in_spec": 0}
            by_param[param]["total"] += 1
            if record.in_spec:
                by_param[param]["in_spec"] += 1
        
        by_parameter = {
            param: {
                "in_spec_percent": Decimal(data["in_spec"] / data["total"] * 100).quantize(Decimal("0.1")),
                "tests_count": data["total"]
            }
            for param, data in by_param.items()
        }
        
        return QualitySummaryResponse(
            average_quality=avg_quality,
            approved_count=approved,
            rejected_count=rejected,
            pending_count=pending,
            defect_rate=defect_rate,
            by_parameter=by_parameter,
            period_from=from_date,
            period_to=to_date
        )
    
    async def get_defect_trends(
        self,
        from_date: date,
        to_date: date
    ) -> DefectTrendsResponse:
        """Get defect trends over time."""
        query = select(QualityResult).where(
            QualityResult.test_date >= from_date,
            QualityResult.test_date <= to_date
        ).order_by(QualityResult.test_date)
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        # Group by date
        by_date: Dict[date, Dict] = {}
        for record in records:
            d = record.test_date
            if d not in by_date:
                by_date[d] = {"total": 0, "rejected": 0}
            by_date[d]["total"] += 1
            if record.decision == "rejected":
                by_date[d]["rejected"] += 1
        
        trends = [
            {
                "trend_date": d,
                "defect_rate": Decimal(data["rejected"] / data["total"] * 100).quantize(Decimal("0.1")) if data["total"] > 0 else Decimal("0"),
                "rejected_count": data["rejected"],
                "total_tests": data["total"]
            }
            for d, data in sorted(by_date.items())
        ]
        
        return DefectTrendsResponse(
            trends=trends,
            period_from=from_date,
            period_to=to_date
        )
    
    async def get_quality_lots(
        self,
        from_date: date,
        to_date: date,
        decision: Optional[str] = None
    ) -> QualityLotsResponse:
        """Get quality lots with decisions."""
        query = select(QualityResult).where(
            QualityResult.test_date >= from_date,
            QualityResult.test_date <= to_date
        )

        if decision:
            query = query.where(QualityResult.decision == decision.lower())

        query = query.order_by(desc(QualityResult.test_date))

        result = await self.db.execute(query)
        records = result.scalars().all()

        # Group by lot
        by_lot: Dict[str, Dict] = {}
        for record in records:
            lot = record.lot_number
            if lot not in by_lot:
                by_lot[lot] = {
                    "product_id": str(record.product_id),
                    "product_name": record.product_name,
                    "decision": record.decision,
                    "test_date": record.test_date,
                    "parameters": []
                }
            by_lot[lot]["parameters"].append({
                "name": record.parameter_name,
                "in_spec": record.in_spec
            })
        
        lots = []
        for lot_number, data in by_lot.items():
            params = data["parameters"]
            passed = sum(1 for p in params if p["in_spec"])
            
            lots.append({
                "lot_number": lot_number,
                "product_id": data["product_id"],
                "product_name": data["product_name"],
                "decision": data["decision"],
                "test_date": data["test_date"],
                "parameters_tested": len(params),
                "parameters_passed": passed
            })
        
        approved_count = sum(1 for l in lots if l["decision"] == "approved")
        rejected_count = sum(1 for l in lots if l["decision"] == "rejected")
        pending_count = sum(1 for l in lots if l["decision"] == "pending")
        
        return QualityLotsResponse(
            lots=lots,
            total=len(lots),
            approved_count=approved_count,
            rejected_count=rejected_count,
            pending_count=pending_count,
            period_from=from_date,
            period_to=to_date
        )

    async def get_parameter_trends(
        self,
        from_date: date,
        to_date: date,
        production_line: Optional[str] = None,
    ) -> ParameterTrendsResponse:
        """Daily quality parameter trends with spec limits, optionally filtered by production line."""
        query = (
            select(
                QualityResult.parameter_name,
                QualityResult.test_date,
                func.avg(QualityResult.result_value).label("avg_value"),
                func.count(QualityResult.id).label("test_count"),
                func.sum(case((QualityResult.in_spec == False, 1), else_=0)).label("out_of_spec_count"),  # noqa: E712
                func.max(QualitySpec.lower_limit).label("lower_limit"),
                func.max(QualitySpec.upper_limit).label("upper_limit"),
            )
            .outerjoin(QualitySpec, QualitySpec.id == QualityResult.quality_spec_id)
            .where(
                QualityResult.test_date >= from_date,
                QualityResult.test_date <= to_date,
            )
        )
        if production_line:
            lot_subquery = (
                select(ProductionOutput.lot_number)
                .join(OrderSnapshot, ProductionOutput.order_id == OrderSnapshot.order_id)
                .where(OrderSnapshot.production_line == production_line)
                .distinct()
                .scalar_subquery()
            )
            query = query.where(QualityResult.lot_number.in_(lot_subquery))

        query = query.group_by(
            QualityResult.parameter_name, QualityResult.test_date
        ).order_by(QualityResult.parameter_name, QualityResult.test_date)

        result = await self.db.execute(query)
        rows = result.all()

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
            from_date=str(from_date),
            to_date=str(to_date),
            production_line=production_line,
            parameter_count=len(parameters),
        )
        return ParameterTrendsResponse(period_from=from_date, period_to=to_date, parameters=parameters)

    async def get_lot_deviations(self, lot_number: str) -> Optional[LotDeviationsResponse]:
        """Return out-of-spec parameter deviations for a specific lot."""
        quality_query = (
            select(
                QualityResult.parameter_name,
                QualityResult.result_value,
                QualitySpec.lower_limit,
                QualitySpec.upper_limit,
            )
            .outerjoin(QualitySpec, QualitySpec.id == QualityResult.quality_spec_id)
            .where(
                QualityResult.lot_number == lot_number,
                QualityResult.in_spec == False,  # noqa: E712
            )
        )
        result = await self.db.execute(quality_query)
        rows = result.all()

        if not rows:
            # Check if lot exists at all
            exists = await self.db.execute(
                select(QualityResult.lot_number).where(QualityResult.lot_number == lot_number).limit(1)
            )
            if not exists.scalar_one_or_none():
                return None
            return LotDeviationsResponse(
                lot_number=lot_number,
                product_name=None,
                shift=None,
                fail_count=0,
                deviations=[],
            )

        deviations: List[LotDeviationItem] = []
        for row in rows:
            result_val = Decimal(str(row.result_value or 0))
            lower = Decimal(str(row.lower_limit)) if row.lower_limit is not None else None
            upper = Decimal(str(row.upper_limit)) if row.upper_limit is not None else None
            if lower is not None and upper is not None:
                magnitude = (
                    (result_val - upper).quantize(Decimal("0.0001"))
                    if result_val > upper
                    else (lower - result_val).quantize(Decimal("0.0001"))
                )
            else:
                magnitude = Decimal("0.0000")
            deviations.append(
                LotDeviationItem(
                    parameter_name=row.parameter_name,
                    result_value=result_val,
                    lower_limit=lower,
                    upper_limit=upper,
                    deviation_magnitude=magnitude,
                )
            )

        # Get production metadata from ProductionOutput
        output_result = await self.db.execute(
            select(ProductionOutput.product_name, ProductionOutput.shift)
            .where(ProductionOutput.lot_number == lot_number)
            .order_by(desc(ProductionOutput.production_date))
            .limit(1)
        )
        output_row = output_result.one_or_none()
        product_name = output_row.product_name if output_row else None
        shift = output_row.shift if output_row else None

        return LotDeviationsResponse(
            lot_number=lot_number,
            product_name=product_name,
            shift=shift,
            fail_count=len(deviations),
            deviations=deviations,
        )

    async def get_defect_pareto(
        self,
        from_date: date,
        to_date: date,
        production_line: Optional[str] = None,
    ) -> DefectParetoResponse:
        """Parameters ranked by out-of-spec count with cumulative %, optionally filtered by line."""
        conditions = [
            QualityResult.test_date >= from_date,
            QualityResult.test_date <= to_date,
        ]
        if production_line:
            lot_subquery = (
                select(ProductionOutput.lot_number)
                .join(OrderSnapshot, ProductionOutput.order_id == OrderSnapshot.order_id)
                .where(OrderSnapshot.production_line == production_line)
                .distinct()
                .scalar_subquery()
            )
            conditions.append(QualityResult.lot_number.in_(lot_subquery))

        query = (
            select(
                QualityResult.parameter_name,
                func.count(QualityResult.id).label("total_tests"),
                func.sum(case((QualityResult.in_spec == False, 1), else_=0)).label("defect_count"),  # noqa: E712
            )
            .where(*conditions)
            .group_by(QualityResult.parameter_name)
            .order_by(func.sum(case((QualityResult.in_spec == False, 1), else_=0)).desc())  # noqa: E712
        )
        result = await self.db.execute(query)
        rows = result.all()

        grand_total = sum(int(row.defect_count or 0) for row in rows)
        running = 0
        parameters: List[ParetoItem] = []
        for row in rows:
            total_tests = int(row.total_tests or 0)
            defect_count = int(row.defect_count or 0)
            running += defect_count
            defect_pct = (
                (Decimal(str(defect_count)) / Decimal(str(total_tests)) * 100).quantize(Decimal("0.01"))
                if total_tests > 0
                else Decimal("0.00")
            )
            cumulative_pct = (
                (Decimal(str(running)) / Decimal(str(grand_total)) * 100).quantize(Decimal("0.01"))
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
            from_date=str(from_date),
            to_date=str(to_date),
            production_line=production_line,
            total_defects=grand_total,
        )
        return DefectParetoResponse(
            period_from=from_date,
            period_to=to_date,
            product_id=None,
            total_defects=grand_total,
            parameters=parameters,
        )

    @track_feature_path(feature_name="quality.sync_from_gateway", log_result=True)
    async def sync_from_gateway(
        self,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> int:
        """Sync quality data from Gateway."""
        logger.info("syncing_quality_from_gateway", from_date=from_date, to_date=to_date)
        
        # Fetch quality results from Gateway (no from/to support — fetch all, filter locally)
        quality_response = await self.gateway.get_quality()

        records_processed = 0
        batch_size = 50

        all_results = quality_response.results
        logger.info("quality_fetched_from_gateway", total_results=len(all_results))

        # Filter by date range locally since Gateway doesn't support from/to for quality
        results = []
        for quality_item in all_results:
            td = quality_item.testDate
            if td and isinstance(td, str):
                try:
                    td_parsed = date.fromisoformat(td[:10])
                except ValueError:
                    td_parsed = None
            elif isinstance(td, date):
                td_parsed = td
            else:
                td_parsed = None
            
            if from_date and td_parsed and td_parsed < from_date:
                continue
            if to_date and td_parsed and td_parsed > to_date:
                continue
            results.append(quality_item)

        logger.info("quality_filtered_by_date", filtered_results=len(results), from_date=from_date, to_date=to_date)

        # Load product names for enrichment
        product_names: Dict[UUID, str] = {}
        product_result = await self.db.execute(select(Product.id, Product.name))
        product_names = {row[0]: row[1] for row in product_result.all()}

        batch = []
        for quality_item in results:
            # Enrich product_name
            product_name = None
            product_id_raw = quality_item.productId
            product_id = None

            if product_id_raw and str(product_id_raw).strip():
                try:
                    product_id = UUID(str(product_id_raw)) if not isinstance(product_id_raw, UUID) else product_id_raw
                    product_name = product_names.get(product_id)
                except (ValueError, AttributeError, TypeError):
                    product_id = uuid4()
            else:
                # Gateway doesn't provide valid product IDs, use lot_number hash
                product_id = uuid4()

            # Parse test date
            test_date_raw = quality_item.testDate
            if isinstance(test_date_raw, str):
                try:
                    test_date_parsed = date.fromisoformat(test_date_raw[:10])
                except ValueError:
                    test_date_parsed = date.today()
            elif isinstance(test_date_raw, date):
                test_date_parsed = test_date_raw
            else:
                test_date_parsed = date.today()

            # Quality spec creation not needed as QualityResultItem doesn't have lowerLimit/upperLimit
            quality_spec_id = None
            parameter_name = quality_item.parameterName or ""

            quality_result = QualityResult(
                id=quality_item.id,
                lot_number=quality_item.lotNumber,
                product_id=product_id,
                product_name=product_name,
                parameter_name=parameter_name,
                result_value=quality_item.resultValue,
                quality_spec_id=quality_spec_id,
                in_spec=True,
                decision=quality_item.qualityStatus.lower() if quality_item.qualityStatus else "pending",
                test_date=test_date_parsed
            )
            batch.append(quality_result)
            
            if len(batch) >= batch_size:
                try:
                    for item in batch: await self.db.merge(item)
                    await self.db.commit()
                    records_processed += len(batch)
                except Exception as e:
                    await self.db.rollback()
                    logger.error("quality_sync_batch_error", error=str(e)[:200])
                batch = []
        
        # Commit remaining records
        if batch:
            try:
                for item in batch: await self.db.merge(item)
                await self.db.commit()
                records_processed += len(batch)
            except Exception as e:
                await self.db.rollback()
                logger.error("quality_sync_final_batch_error", error=str(e)[:200])
        
        log_data_flow(
            source="quality_service",
            target="database",
            operation="sync_insert",
            records_count=records_processed,
        )
        logger.info("quality_sync_completed", records_processed=records_processed)
        return records_processed

    async def upsert_from_event(self, payload: "QualityResultRecordedPayload", event_id: str = None) -> None:
        """Upsert quality result from event. Idempotent by event_id or lot_number.

        Note: parameter_name and test_date are NOT NULL in DB but absent from event.
        Defaults: parameter_name='from_event', test_date=date.today().
        Hourly cron will overwrite with real values on next run.
        """
        from app.messaging.schemas import QualityResultRecordedPayload

        # First check by event_id if provided (absolute idempotency)
        if event_id:
            result = await self.db.execute(
                select(QualityResult).where(QualityResult.event_id == UUID(event_id))
            )
            quality = result.scalar_one_or_none()
            if quality:
                logger.info("quality_result_skipped_duplicate_event", event_id=event_id)
                return

        result = await self.db.execute(
            select(QualityResult).where(QualityResult.lot_number == payload.lot_number)
        )
        quality = result.scalar_one_or_none()

        # Sync QualitySpec if present
        quality_spec_id = None
        if hasattr(payload, 'qualitySpec') and payload.qualitySpec and hasattr(payload, 'product_id') and hasattr(payload, 'parameter_name'):
            try:
                product_uuid = UUID(payload.product_id) if isinstance(payload.product_id, str) else payload.product_id
                quality_spec_id = await self._sync_quality_spec(product_uuid, payload.parameter_name, payload.qualitySpec)
            except (ValueError, AttributeError, TypeError):
                logger.warning("invalid_product_id_for_spec_event", raw=payload.product_id)

        if quality:
            quality.in_spec = payload.in_spec
            quality.decision = payload.quality_status.lower()
            if quality_spec_id:
                quality.quality_spec_id = quality_spec_id
            if event_id:
                quality.event_id = UUID(event_id)
            logger.info(
                "quality_result_updated_from_event",
                lot_number=payload.lot_number,
                decision=payload.quality_status,
            )
        else:
            quality = QualityResult(
                id=payload.id,
                lot_number=payload.lot_number,
                product_id=payload.product_id,
                quality_spec_id=quality_spec_id,
                in_spec=payload.in_spec,
                decision=payload.quality_status.lower(),
                parameter_name="from_event",
                test_date=date.today(),
                event_id=UUID(event_id) if event_id else None,
            )
            self.db.add(quality)
            logger.info(
                "quality_result_inserted_from_event",
                lot_number=payload.lot_number,
                decision=payload.quality_status,
            )

        await self.db.commit()
