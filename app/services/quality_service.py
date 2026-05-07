"""
Quality business logic service.
"""
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import select, func, desc, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import QualityResult, Product
from app.schemas import QualitySummaryResponse, DefectTrendsResponse, QualityLotsResponse
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
import structlog

logger = structlog.get_logger()


class QualityService:
    """Service for quality business logic."""
    
    def __init__(self, db: AsyncSession, gateway: GatewayClient):
        self.db = db
        self.gateway = gateway
    
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
        # Join with Product to get product_name using source_system_id
        query = select(
            QualityResult,
            Product.name.label("product_name")
        ).outerjoin(
            Product, cast(QualityResult.product_id, String) == Product.source_system_id
        ).where(
            QualityResult.test_date >= from_date,
            QualityResult.test_date <= to_date
        )
        
        if decision:
            query = query.where(QualityResult.decision == decision.lower())
        
        query = query.order_by(desc(QualityResult.test_date))
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # Group by lot
        by_lot: Dict[str, Dict] = {}
        for row in rows:
            record = row.QualityResult
            lot = record.lot_number
            if lot not in by_lot:
                by_lot[lot] = {
                    "product_id": str(record.product_id),
                    "product_name": row.product_name or record.product_name,
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
    
    @track_feature_path(feature_name="quality.sync_from_gateway", log_result=True)
    @track_feature_path(feature_name="quality.sync_from_gateway", log_result=True)
    async def sync_from_gateway(
        self,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> int:
        """Sync quality data from Gateway."""
        logger.info("syncing_quality_from_gateway", from_date=from_date, to_date=to_date)
        
        # Fetch quality results from Gateway (no from/to support — fetch all, filter locally)
        gateway_data = await self.gateway.get_quality()
        
        records_processed = 0
        batch_size = 50
        
        # Gateway returns results under "results" key
        all_results = gateway_data.get("results", gateway_data.get("quality", []))
        logger.info("quality_fetched_from_gateway", total_results=len(all_results))
        
        # Filter by date range locally since Gateway doesn't support from/to for quality
        results = []
        for r in all_results:
            td = r.get("testDate")
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
            results.append(r)
        
        logger.info("quality_filtered_by_date", filtered_results=len(results), from_date=from_date, to_date=to_date)
        
        batch = []
        for result in results:
            # Parse ISO datetime string to date
            test_date_raw = result.get("testDate", date.today())
            if isinstance(test_date_raw, str):
                try:
                    test_date_parsed = date.fromisoformat(test_date_raw[:10])
                except ValueError:
                    test_date_parsed = date.today()
            elif isinstance(test_date_raw, date):
                test_date_parsed = test_date_raw
            else:
                test_date_parsed = date.today()
            
            quality_result = QualityResult(
                lot_number=result.get("lotNumber", ""),
                product_id=result.get("productId"),
                product_name=None,
                parameter_name=result.get("parameterName", ""),
                result_value=result.get("resultValue"),
                lower_limit=result.get("lowerLimit"),
                upper_limit=result.get("upperLimit"),
                in_spec=result.get("inSpec", True),
                decision=result.get("decision", "pending").lower(),
                test_date=test_date_parsed
            )
            batch.append(quality_result)
            
            if len(batch) >= batch_size:
                try:
                    self.db.add_all(batch)
                    await self.db.commit()
                    records_processed += len(batch)
                except Exception as e:
                    await self.db.rollback()
                    logger.error("quality_sync_batch_error", error=str(e)[:200])
                batch = []
        
        # Commit remaining records
        if batch:
            try:
                self.db.add_all(batch)
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
