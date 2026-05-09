"""
Finance Manager Dashboard service.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.sales import AggregatedSales, SalesTrends, SaleRecord
from app.schemas.finance_dashboard import (
    GroupByType,
    IntervalType,
    SortBy,
    SalesGroupItem,
    SalesBreakdownResponse,
    RevenueTrendPoint,
    RevenueTrendResponse,
    TopProductItem,
    TopProductsResponse,
)

logger = structlog.get_logger()


class FinanceManagerDashboardService:
    """Provides revenue and sales analytics for Finance Managers."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_sales_breakdown(
        self,
        date_from: date,
        date_to: date,
        group_by: GroupByType,
    ) -> SalesBreakdownResponse:
        """
        Return revenue breakdown by channel, region, or product.

        Reads from AggregatedSales where group_by_type matches the requested dimension.
        Rows whose period_from falls within [date_from, date_to] are included.
        Groups are ranked descending by total_amount.
        """
        query = (
            select(
                AggregatedSales.group_key,
                func.sum(AggregatedSales.total_amount).label("total_amount"),
                func.sum(AggregatedSales.total_quantity).label("total_quantity"),
                func.sum(AggregatedSales.sales_count).label("sales_count"),
            )
            .where(
                AggregatedSales.group_by_type == group_by.value,
                AggregatedSales.period_from >= date_from,
                AggregatedSales.period_from <= date_to,
            )
            .group_by(AggregatedSales.group_key)
            .order_by(func.sum(AggregatedSales.total_amount).desc())
        )
        result = await self.db.execute(query)
        rows = result.all()

        grand_amount = sum((Decimal(str(row.total_amount or 0)) for row in rows), Decimal("0"))

        groups: List[SalesGroupItem] = []
        for row in rows:
            total_amount = Decimal(str(row.total_amount or 0)).quantize(Decimal("0.01"))
            total_quantity = Decimal(str(row.total_quantity or 0)).quantize(Decimal("0.001"))
            sales_count = int(row.sales_count or 0)
            avg_order_value = (
                (total_amount / Decimal(str(sales_count))).quantize(Decimal("0.01"))
                if sales_count > 0
                else Decimal("0.00")
            )
            amount_share = (
                (total_amount / grand_amount * 100).quantize(Decimal("0.01"))
                if grand_amount > 0
                else Decimal("0.00")
            )
            groups.append(
                SalesGroupItem(
                    group_key=row.group_key,
                    total_amount=total_amount,
                    total_quantity=total_quantity,
                    sales_count=sales_count,
                    avg_order_value=avg_order_value,
                    amount_share_pct=amount_share,
                )
            )

        grand_quantity = sum(g.total_quantity for g in groups)

        logger.info(
            "sales_breakdown_calculated",
            date_from=str(date_from),
            date_to=str(date_to),
            group_by=group_by.value,
            group_count=len(groups),
        )

        return SalesBreakdownResponse(
            period_from=date_from,
            period_to=date_to,
            group_by=group_by,
            total_amount=grand_amount.quantize(Decimal("0.01")),
            total_quantity=grand_quantity,
            groups=groups,
        )

    async def get_revenue_trend(
        self,
        date_from: date,
        date_to: date,
        interval: IntervalType,
        region: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> RevenueTrendResponse:
        """
        Return revenue trend data points for the given interval and optional filters.

        Reads from SalesTrends. MoM (period-over-period) growth computed in Python.
        """
        conditions = [
            SalesTrends.interval_type == interval.value,
            SalesTrends.trend_date >= date_from,
            SalesTrends.trend_date <= date_to,
        ]
        if region is not None:
            conditions.append(SalesTrends.region == region)
        else:
            conditions.append(SalesTrends.region.is_(None))

        if channel is not None:
            conditions.append(SalesTrends.channel == channel)
        else:
            conditions.append(SalesTrends.channel.is_(None))

        query = (
            select(
                SalesTrends.trend_date,
                SalesTrends.total_amount,
                SalesTrends.total_quantity,
                SalesTrends.order_count,
            )
            .where(*conditions)
            .order_by(SalesTrends.trend_date)
        )
        result = await self.db.execute(query)
        rows = result.all()

        data: List[RevenueTrendPoint] = []
        prev_amount: Optional[Decimal] = None
        for row in rows:
            total_amount = Decimal(str(row.total_amount or 0)).quantize(Decimal("0.01"))
            total_quantity = Decimal(str(row.total_quantity or 0)).quantize(Decimal("0.001"))
            if prev_amount is not None and prev_amount > 0:
                mom_growth: Optional[Decimal] = (
                    (total_amount - prev_amount) / prev_amount * 100
                ).quantize(Decimal("0.01"))
            else:
                mom_growth = None
            data.append(
                RevenueTrendPoint(
                    trend_date=row.trend_date,
                    total_amount=total_amount,
                    total_quantity=total_quantity,
                    order_count=int(row.order_count or 0),
                    mom_growth_pct=mom_growth,
                )
            )
            prev_amount = total_amount

        logger.info(
            "revenue_trend_calculated",
            date_from=str(date_from),
            date_to=str(date_to),
            interval=interval.value,
            region=region,
            channel=channel,
            point_count=len(data),
        )

        return RevenueTrendResponse(
            period_from=date_from,
            period_to=date_to,
            interval=interval,
            region=region,
            channel=channel,
            data=data,
        )

    async def get_top_products(
        self,
        date_from: date,
        date_to: date,
        limit: int = 10,
        sort_by: SortBy = SortBy.amount,
    ) -> TopProductsResponse:
        """
        Return top products ranked by amount or quantity.

        Reads from SaleRecord, groups by product_name (denormalized for simplicity).
        """
        sort_col = (
            func.sum(SaleRecord.amount).desc()
            if sort_by == SortBy.amount
            else func.sum(SaleRecord.quantity).desc()
        )

        query = (
            select(
                SaleRecord.product_name,
                func.sum(SaleRecord.amount).label("total_amount"),
                func.sum(SaleRecord.quantity).label("total_quantity"),
                func.count(SaleRecord.id).label("sales_count"),
            )
            .where(
                SaleRecord.sale_date >= date_from,
                SaleRecord.sale_date <= date_to,
            )
            .group_by(SaleRecord.product_name)
            .order_by(sort_col)
            .limit(limit)
        )
        result = await self.db.execute(query)
        rows = result.all()

        # Grand total (all products, not just top-N) for share calculation
        total_query = (
            select(func.sum(SaleRecord.amount).label("grand_total"))
            .where(
                SaleRecord.sale_date >= date_from,
                SaleRecord.sale_date <= date_to,
            )
        )
        total_result = await self.db.execute(total_query)
        grand_total = Decimal(str(total_result.scalar() or 0)).quantize(Decimal("0.01"))

        products: List[TopProductItem] = []
        for rank, row in enumerate(rows, start=1):
            total_amount = Decimal(str(row.total_amount or 0)).quantize(Decimal("0.01"))
            total_quantity = Decimal(str(row.total_quantity or 0)).quantize(Decimal("0.001"))
            amount_share = (
                (total_amount / grand_total * 100).quantize(Decimal("0.01"))
                if grand_total > 0
                else Decimal("0.00")
            )
            products.append(
                TopProductItem(
                    rank=rank,
                    product_name=row.product_name or "Unknown",
                    total_amount=total_amount,
                    total_quantity=total_quantity,
                    sales_count=int(row.sales_count or 0),
                    amount_share_pct=amount_share,
                )
            )

        logger.info(
            "top_products_calculated",
            date_from=str(date_from),
            date_to=str(date_to),
            sort_by=sort_by.value,
            limit=limit,
            product_count=len(products),
        )

        return TopProductsResponse(
            period_from=date_from,
            period_to=date_to,
            sort_by=sort_by,
            total_amount=grand_total,
            products=products,
        )
