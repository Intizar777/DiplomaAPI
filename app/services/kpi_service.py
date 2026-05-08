"""
KPI business logic service.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AggregatedKPI, ProductionLine
from app.schemas import KPICurrentResponse, KPIHistoryResponse, KPICompareResponse
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
import structlog

logger = structlog.get_logger()


class KPIService:
    """Service for KPI business logic."""
    
    def __init__(self, db: AsyncSession, gateway: GatewayClient):
        self.db = db
        self.gateway = gateway
    
    async def get_current_kpi(
        self,
        production_line: Optional[str] = None
    ) -> KPICurrentResponse:
        """Get current KPI (last completed period)."""
        # Get most recent record
        query = select(AggregatedKPI).order_by(AggregatedKPI.period_to.desc())
        
        if production_line:
            query = query.where(AggregatedKPI.production_line == production_line)
        
        query = query.limit(1)
        result = await self.db.execute(query)
        kpi = result.scalar_one_or_none()
        
        if not kpi:
            # Return empty/default response
            today = date.today()
            return KPICurrentResponse(
                data={
                    "total_output": Decimal("0"),
                    "defect_rate": Decimal("0"),
                    "completed_orders": 0,
                    "total_orders": 0,
                    "oee_estimate": None,
                    "production_line": production_line
                },
                period_from=today - timedelta(days=30),
                period_to=today
            )
        
        return KPICurrentResponse(
            data={
                "total_output": kpi.total_output,
                "defect_rate": kpi.defect_rate,
                "completed_orders": kpi.completed_orders,
                "total_orders": kpi.total_orders,
                "oee_estimate": kpi.oee_estimate,
                "production_line": kpi.production_line
            },
            period_from=kpi.period_from,
            period_to=kpi.period_to
        )
    
    async def get_kpi_history(
        self,
        from_date: date,
        to_date: date,
        production_line: Optional[str] = None
    ) -> KPIHistoryResponse:
        """Get KPI history for period."""
        query = select(AggregatedKPI).where(
            AggregatedKPI.period_from >= from_date,
            AggregatedKPI.period_to <= to_date
        ).order_by(AggregatedKPI.period_from)
        
        if production_line:
            query = query.where(AggregatedKPI.production_line == production_line)
        
        result = await self.db.execute(query)
        kpis = result.scalars().all()
        
        items = [
            {
                "period_from": kpi.period_from,
                "period_to": kpi.period_to,
                "production_line": kpi.production_line,
                "total_output": kpi.total_output,
                "defect_rate": kpi.defect_rate,
                "completed_orders": kpi.completed_orders,
                "total_orders": kpi.total_orders,
                "oee_estimate": kpi.oee_estimate
            }
            for kpi in kpis
        ]
        
        return KPIHistoryResponse(
            items=items,
            period_from=from_date,
            period_to=to_date
        )
    
    async def get_all_kpi(
        self,
        production_line: Optional[str] = None
    ) -> KPIHistoryResponse:
        """Get all KPI records (no date filter)."""
        query = select(AggregatedKPI).order_by(AggregatedKPI.period_from)
        
        if production_line:
            query = query.where(AggregatedKPI.production_line == production_line)
        
        result = await self.db.execute(query)
        kpis = result.scalars().all()
        
        items = [
            {
                "period_from": kpi.period_from,
                "period_to": kpi.period_to,
                "production_line": kpi.production_line,
                "total_output": kpi.total_output,
                "defect_rate": kpi.defect_rate,
                "completed_orders": kpi.completed_orders,
                "total_orders": kpi.total_orders,
                "oee_estimate": kpi.oee_estimate
            }
            for kpi in kpis
        ]
        
        period_from = kpis[0].period_from if kpis else date.today()
        period_to = kpis[-1].period_to if kpis else date.today()
        
        return KPIHistoryResponse(
            items=items,
            period_from=period_from,
            period_to=period_to
        )
    
    async def compare_kpi_periods(
        self,
        period1_from: date,
        period1_to: date,
        period2_from: date,
        period2_to: date
    ) -> KPICompareResponse:
        """Compare KPI between two periods."""
        # Get data for period 1
        query1 = select(AggregatedKPI).where(
            AggregatedKPI.period_from == period1_from,
            AggregatedKPI.period_to == period1_to
        )
        result1 = await self.db.execute(query1)
        kpi1 = result1.scalar_one_or_none()
        
        # Get data for period 2
        query2 = select(AggregatedKPI).where(
            AggregatedKPI.period_from == period2_from,
            AggregatedKPI.period_to == period2_to
        )
        result2 = await self.db.execute(query2)
        kpi2 = result2.scalar_one_or_none()
        
        # Default values if not found
        def make_data(kpi, p_from, p_to):
            if kpi:
                return {
                    "period_from": kpi.period_from,
                    "period_to": kpi.period_to,
                    "total_output": kpi.total_output,
                    "defect_rate": kpi.defect_rate,
                    "completed_orders": kpi.completed_orders,
                    "total_orders": kpi.total_orders,
                    "oee_estimate": kpi.oee_estimate
                }
            return {
                "period_from": p_from,
                "period_to": p_to,
                "total_output": Decimal("0"),
                "defect_rate": Decimal("0"),
                "completed_orders": 0,
                "total_orders": 0,
                "oee_estimate": None
            }
        
        data1 = make_data(kpi1, period1_from, period1_to)
        data2 = make_data(kpi2, period2_from, period2_to)
        
        # Calculate changes
        output_change = Decimal("0")
        if data2["total_output"] > 0:
            output_change = ((data1["total_output"] - data2["total_output"]) 
                           / data2["total_output"] * 100)
        
        defect_change = data1["defect_rate"] - data2["defect_rate"]
        
        completion_change = Decimal("0")
        if data2["total_orders"] > 0:
            completion2 = Decimal(data2["completed_orders"]) / data2["total_orders"] * 100
            completion1 = Decimal(data1["completed_orders"]) / data1["total_orders"] * 100 if data1["total_orders"] > 0 else Decimal("0")
            completion_change = completion1 - completion2
        
        return KPICompareResponse(
            period1=data1,
            period2=data2,
            output_change_percent=output_change,
            defect_rate_change=defect_change,
            order_completion_change=completion_change
        )
    
    @track_feature_path(feature_name="kpi.sync_from_gateway", log_result=True)
    async def sync_from_gateway(
        self,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> int:
        """Sync KPI data from Gateway and store aggregated results.
        
        If no dates provided (initial sync), fetches KPI for each month
        from 2024-01 to current month.
        """
        logger.info("syncing_kpi_from_gateway", from_date=from_date, to_date=to_date)
        
        records_processed = 0
        
        if from_date and to_date:
            # Incremental sync: single period (upsert)
            gateway_data = await self.gateway.get_kpi(from_date, to_date)
            kpi_data = gateway_data.get("kpi", gateway_data)
            
            if not kpi_data:
                logger.warning("kpi_sync_no_data_from_gateway")
                return 0
            
            # Use ON CONFLICT DO UPDATE for upsert
            from sqlalchemy.dialects.postgresql import insert
            stmt = insert(AggregatedKPI).values(
                period_from=from_date,
                period_to=to_date,
                production_line=None,
                total_output=Decimal(str(kpi_data.get("totalOutput", 0))),
                defect_rate=Decimal(str(kpi_data.get("defectRate", 0))),
                completed_orders=kpi_data.get("completedOrders", 0),
                total_orders=kpi_data.get("totalOrders", 0),
                oee_estimate=Decimal(str(kpi_data.get("oeeEstimate", 0))) if kpi_data.get("oeeEstimate") else None
            ).on_conflict_do_update(
                index_elements=['period_from', 'period_to', 'production_line'],
                set_=dict(
                    total_output=Decimal(str(kpi_data.get("totalOutput", 0))),
                    defect_rate=Decimal(str(kpi_data.get("defectRate", 0))),
                    completed_orders=kpi_data.get("completedOrders", 0),
                    total_orders=kpi_data.get("totalOrders", 0),
                    oee_estimate=Decimal(str(kpi_data.get("oeeEstimate", 0))) if kpi_data.get("oeeEstimate") else None
                )
            )
            await self.db.execute(stmt)
            logger.info("kpi_sync_upserted", period_from=from_date.isoformat(), period_to=to_date.isoformat())
            
            await self.db.commit()
            records_processed += 1
        else:
            # Initial sync: fetch KPI for each month from 2024-01 to now
            from calendar import monthrange
            
            start = date(2024, 1, 1)
            end = date.today()
            
            current = start
            while current <= end:
                year = current.year
                month = current.month
                last_day = monthrange(year, month)[1]
                month_start = date(year, month, 1)
                month_end = date(year, month, last_day)
                
                try:
                    gateway_data = await self.gateway.get_kpi(from_date=month_start, to_date=month_end)
                    kpi_data = gateway_data.get("kpi", gateway_data)
                    
                    if kpi_data and kpi_data.get("totalOrders", 0) > 0:
                        aggregated = AggregatedKPI(
                            period_from=month_start,
                            period_to=month_end,
                            production_line=None,
                            total_output=Decimal(str(kpi_data.get("totalOutput", 0))),
                            defect_rate=Decimal(str(kpi_data.get("defectRate", 0))),
                            completed_orders=kpi_data.get("completedOrders", 0),
                            total_orders=kpi_data.get("totalOrders", 0),
                            oee_estimate=Decimal(str(kpi_data.get("oeeEstimate", 0))) if kpi_data.get("oeeEstimate") else None
                        )
                        self.db.add(aggregated)
                        records_processed += 1
                        logger.info("kpi_sync_month", month=month_start.isoformat(), total_orders=kpi_data.get("totalOrders", 0))
                except Exception as e:
                    logger.error("kpi_sync_month_error", month=month_start.isoformat(), error=str(e)[:200])
                
                # Move to next month
                if month == 12:
                    current = date(year + 1, 1, 1)
                else:
                    current = date(year, month + 1, 1)
            
            await self.db.commit()
        
        log_data_flow(
            source="kpi_service",
            target="database",
            operation="sync_insert",
            records_count=records_processed,
        )
        logger.info("kpi_sync_completed", records_processed=records_processed)
        return records_processed

    @track_feature_path(feature_name="kpi.sync_per_line", log_result=True)
    async def sync_kpi_per_line(
        self,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> int:
        """Sync KPI data from Gateway for each production line.

        Fetches KPI for each active production line and stores separately.
        If no dates provided (initial sync), fetches KPI for each month
        from 2024-01 to current month.
        """
        logger.info(
            "syncing_kpi_per_line_from_gateway",
            from_date=from_date,
            to_date=to_date
        )

        records_processed = 0

        # Get all active production lines
        query = select(ProductionLine).where(ProductionLine.is_active == True)
        result = await self.db.execute(query)
        production_lines = result.scalars().all()

        if not production_lines:
            logger.warning("no_active_production_lines_found")
            return 0

        line_codes = [pl.code for pl in production_lines if pl.code]
        logger.info("kpi_sync_per_line_found_lines", lines_count=len(line_codes), lines=line_codes)

        if from_date and to_date:
            # Incremental sync: fetch for each line (upsert)
            for line_code in line_codes:
                try:
                    gateway_data = await self.gateway.get_kpi(from_date, to_date, line_code)
                    kpi_data = gateway_data.get("kpi", gateway_data)

                    if not kpi_data:
                        logger.debug("kpi_sync_no_data_for_line", line=line_code)
                        continue

                    # Use ON CONFLICT DO UPDATE for upsert
                    from sqlalchemy.dialects.postgresql import insert
                    stmt = insert(AggregatedKPI).values(
                        period_from=from_date,
                        period_to=to_date,
                        production_line=line_code,
                        total_output=Decimal(str(kpi_data.get("totalOutput", 0))),
                        defect_rate=Decimal(str(kpi_data.get("defectRate", 0))),
                        completed_orders=kpi_data.get("completedOrders", 0),
                        total_orders=kpi_data.get("totalOrders", 0),
                        oee_estimate=Decimal(str(kpi_data.get("oeeEstimate", 0))) if kpi_data.get("oeeEstimate") else None
                    ).on_conflict_do_update(
                        index_elements=['period_from', 'period_to', 'production_line'],
                        set_=dict(
                            total_output=Decimal(str(kpi_data.get("totalOutput", 0))),
                            defect_rate=Decimal(str(kpi_data.get("defectRate", 0))),
                            completed_orders=kpi_data.get("completedOrders", 0),
                            total_orders=kpi_data.get("totalOrders", 0),
                            oee_estimate=Decimal(str(kpi_data.get("oeeEstimate", 0))) if kpi_data.get("oeeEstimate") else None
                        )
                    )
                    await self.db.execute(stmt)
                    records_processed += 1
                    logger.info(
                        "kpi_sync_per_line_upserted",
                        line=line_code,
                        period_from=from_date.isoformat(),
                        period_to=to_date.isoformat()
                    )
                except Exception as e:
                    logger.error(
                        "kpi_sync_per_line_error",
                        line=line_code,
                        error=str(e)[:200]
                    )

            await self.db.commit()
        else:
            # Initial sync: fetch for each month and each line
            from calendar import monthrange

            start = date(2024, 1, 1)
            end = date.today()

            current = start
            while current <= end:
                year = current.year
                month = current.month
                last_day = monthrange(year, month)[1]
                month_start = date(year, month, 1)
                month_end = date(year, month, last_day)

                for line_code in line_codes:
                    try:
                        gateway_data = await self.gateway.get_kpi(
                            from_date=month_start,
                            to_date=month_end,
                            production_line=line_code
                        )
                        kpi_data = gateway_data.get("kpi", gateway_data)

                        if kpi_data and kpi_data.get("totalOrders", 0) > 0:
                            aggregated = AggregatedKPI(
                                period_from=month_start,
                                period_to=month_end,
                                production_line=line_code,
                                total_output=Decimal(str(kpi_data.get("totalOutput", 0))),
                                defect_rate=Decimal(str(kpi_data.get("defectRate", 0))),
                                completed_orders=kpi_data.get("completedOrders", 0),
                                total_orders=kpi_data.get("totalOrders", 0),
                                oee_estimate=Decimal(str(kpi_data.get("oeeEstimate", 0))) if kpi_data.get("oeeEstimate") else None
                            )
                            self.db.add(aggregated)
                            records_processed += 1
                    except Exception as e:
                        logger.error(
                            "kpi_sync_per_line_month_error",
                            month=month_start.isoformat(),
                            line=line_code,
                            error=str(e)[:200]
                        )

                # Move to next month
                if month == 12:
                    current = date(year + 1, 1, 1)
                else:
                    current = date(year, month + 1, 1)

            await self.db.commit()

        log_data_flow(
            source="kpi_service",
            target="database",
            operation="sync_per_line_insert",
            records_count=records_processed,
        )
        logger.info("kpi_sync_per_line_completed", records_processed=records_processed)
        return records_processed
