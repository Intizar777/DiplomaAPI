"""
Unit tests for FinanceManagerDashboardService.

Uses testcontainers PostgreSQL (real DB, not mocks).
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio

from app.models.sales import AggregatedSales, SalesTrends, SaleRecord
from app.services.finance_dashboard_service import FinanceManagerDashboardService
from app.schemas.finance_dashboard import (
    GroupByType,
    IntervalType,
    SortBy,
    SalesBreakdownResponse,
    RevenueTrendResponse,
    TopProductsResponse,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sample_aggregated_sales(session):
    """
    Insert AggregatedSales rows:
      - group_by_type='channel': wholesale=3100000, retail=2100000
      - group_by_type='region':  north=2500000, south=2700000
    All with period_from = today - 15 (within 30-day window).
    Plus 1 old row (outside window, channel='direct', amount=999999).
    """
    today = date.today()
    period_from = today - timedelta(days=15)
    old_from = today - timedelta(days=60)

    rows = [
        AggregatedSales(
            period_from=period_from, period_to=today,
            group_by_type="channel", group_key="wholesale",
            total_quantity=Decimal("29000"), total_amount=Decimal("3100000"),
            sales_count=140, avg_order_value=Decimal("22142.86"),
        ),
        AggregatedSales(
            period_from=period_from, period_to=today,
            group_by_type="channel", group_key="retail",
            total_quantity=Decimal("19500"), total_amount=Decimal("2100000"),
            sales_count=320, avg_order_value=Decimal("6562.50"),
        ),
        AggregatedSales(
            period_from=period_from, period_to=today,
            group_by_type="region", group_key="north",
            total_quantity=Decimal("22000"), total_amount=Decimal("2500000"),
            sales_count=180, avg_order_value=Decimal("13888.89"),
        ),
        AggregatedSales(
            period_from=period_from, period_to=today,
            group_by_type="region", group_key="south",
            total_quantity=Decimal("26000"), total_amount=Decimal("2700000"),
            sales_count=200, avg_order_value=Decimal("13500.00"),
        ),
        # old row outside 30-day window
        AggregatedSales(
            period_from=old_from, period_to=old_from + timedelta(days=30),
            group_by_type="channel", group_key="direct",
            total_quantity=Decimal("1000"), total_amount=Decimal("999999"),
            sales_count=10, avg_order_value=Decimal("99999.90"),
        ),
    ]
    for r in rows:
        session.add(r)
    await session.commit()
    return rows


@pytest_asyncio.fixture
async def sample_sales_trends(session):
    """
    Insert SalesTrends rows with interval_type='week', region=None, channel=None:
      - week 1: amount=1000000, qty=10000, orders=50
      - week 2: amount=1200000, qty=12000, orders=60  (MoM +20%)
      - week 3: amount=1100000, qty=11000, orders=55  (MoM ~-8.33%)
    Plus 1 row with channel='wholesale' (should be excluded without filter).
    """
    today = date.today()
    w1 = today - timedelta(days=21)
    w2 = today - timedelta(days=14)
    w3 = today - timedelta(days=7)

    rows = [
        SalesTrends(
            trend_date=w1, interval_type="week", region=None, channel=None,
            total_amount=Decimal("1000000"), total_quantity=Decimal("10000"), order_count=50,
        ),
        SalesTrends(
            trend_date=w2, interval_type="week", region=None, channel=None,
            total_amount=Decimal("1200000"), total_quantity=Decimal("12000"), order_count=60,
        ),
        SalesTrends(
            trend_date=w3, interval_type="week", region=None, channel=None,
            total_amount=Decimal("1100000"), total_quantity=Decimal("11000"), order_count=55,
        ),
        SalesTrends(
            trend_date=w2, interval_type="week", region=None, channel="wholesale",
            total_amount=Decimal("800000"), total_quantity=Decimal("8000"), order_count=40,
        ),
    ]
    for r in rows:
        session.add(r)
    await session.commit()
    return rows


@pytest_asyncio.fixture
async def sample_sale_records(session):
    """
    Insert SaleRecord rows:
      - Product Alpha: 3 records, amount = 500000+600000+700000 = 1800000
      - Product Beta: 2 records, amount = 300000+400000 = 700000
      - Product Gamma: 1 record, amount = 200000
    All with sale_date = today - 5.
    Plus 1 old record (today-60, outside 30-day window).
    """
    from uuid import uuid4
    today = date.today()
    recent = today - timedelta(days=5)
    old = today - timedelta(days=60)

    pid_a = uuid4()
    pid_b = uuid4()
    pid_c = uuid4()
    pid_old = uuid4()

    rows = [
        SaleRecord(product_id=pid_a, product_name="Product Alpha",
                   amount=Decimal("500000"), quantity=Decimal("5000"),
                   sale_date=recent, snapshot_date=today),
        SaleRecord(product_id=pid_a, product_name="Product Alpha",
                   amount=Decimal("600000"), quantity=Decimal("6000"),
                   sale_date=recent, snapshot_date=today),
        SaleRecord(product_id=pid_a, product_name="Product Alpha",
                   amount=Decimal("700000"), quantity=Decimal("7000"),
                   sale_date=recent, snapshot_date=today),
        SaleRecord(product_id=pid_b, product_name="Product Beta",
                   amount=Decimal("300000"), quantity=Decimal("3000"),
                   sale_date=recent, snapshot_date=today),
        SaleRecord(product_id=pid_b, product_name="Product Beta",
                   amount=Decimal("400000"), quantity=Decimal("4000"),
                   sale_date=recent, snapshot_date=today),
        SaleRecord(product_id=pid_c, product_name="Product Gamma",
                   amount=Decimal("200000"), quantity=Decimal("2000"),
                   sale_date=recent, snapshot_date=today),
        # old, outside window
        SaleRecord(product_id=pid_old, product_name="Old Product",
                   amount=Decimal("9999999"), quantity=Decimal("99999"),
                   sale_date=old, snapshot_date=today),
    ]
    for r in rows:
        session.add(r)
    await session.commit()
    return rows


# ---------------------------------------------------------------------------
# Sales breakdown tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sales_breakdown_returns_correct_groups(session, sample_aggregated_sales):
    """Should return 2 channel groups (wholesale + retail), ranked desc by amount."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_sales_breakdown(today - timedelta(days=30), today, GroupByType.channel)

    assert isinstance(result, SalesBreakdownResponse)
    assert len(result.groups) == 2
    assert result.groups[0].group_key == "wholesale"
    assert result.groups[1].group_key == "retail"


@pytest.mark.asyncio
async def test_sales_breakdown_amount_share_sums_to_100(session, sample_aggregated_sales):
    """amount_share_pct across all groups should sum to ~100.00."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_sales_breakdown(today - timedelta(days=30), today, GroupByType.channel)

    total_share = sum(g.amount_share_pct for g in result.groups)
    assert total_share == Decimal("100.00")


@pytest.mark.asyncio
async def test_sales_breakdown_excludes_old_records(session, sample_aggregated_sales):
    """'direct' channel row (today-60) must not appear in 30-day window."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_sales_breakdown(today - timedelta(days=30), today, GroupByType.channel)

    group_keys = {g.group_key for g in result.groups}
    assert "direct" not in group_keys


@pytest.mark.asyncio
async def test_sales_breakdown_region_grouping(session, sample_aggregated_sales):
    """group_by=region should return north + south groups."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_sales_breakdown(today - timedelta(days=30), today, GroupByType.region)

    assert len(result.groups) == 2
    group_keys = {g.group_key for g in result.groups}
    assert group_keys == {"north", "south"}


# ---------------------------------------------------------------------------
# Revenue trend tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_revenue_trend_returns_correct_points(session, sample_sales_trends):
    """Should return 3 weekly data points, first mom_growth_pct=None."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_revenue_trend(today - timedelta(days=30), today, IntervalType.week)

    assert isinstance(result, RevenueTrendResponse)
    assert len(result.data) == 3
    assert result.data[0].mom_growth_pct is None


@pytest.mark.asyncio
async def test_revenue_trend_mom_growth_calculated(session, sample_sales_trends):
    """Week 2 vs week 1: (1200000-1000000)/1000000*100 = 20.00%."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_revenue_trend(today - timedelta(days=30), today, IntervalType.week)

    assert result.data[1].mom_growth_pct == Decimal("20.00")


@pytest.mark.asyncio
async def test_revenue_trend_channel_filter_excludes_other_channels(session, sample_sales_trends):
    """No channel filter (None) should not include wholesale-channel rows as extra points."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_revenue_trend(today - timedelta(days=30), today, IntervalType.week)

    # 3 rows with channel=None; the wholesale row has channel='wholesale', excluded
    assert len(result.data) == 3


# ---------------------------------------------------------------------------
# Top products tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_top_products_ranked_by_amount(session, sample_sale_records):
    """Products should be ranked by total_amount desc; Alpha first."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_top_products(today - timedelta(days=30), today, sort_by=SortBy.amount)

    assert isinstance(result, TopProductsResponse)
    assert result.products[0].product_name == "Product Alpha"
    assert result.products[0].rank == 1


@pytest.mark.asyncio
async def test_top_products_excludes_old_records(session, sample_sale_records):
    """'Old Product' (today-60) must not appear in 30-day window."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_top_products(today - timedelta(days=30), today)

    names = {p.product_name for p in result.products}
    assert "Old Product" not in names


@pytest.mark.asyncio
async def test_top_products_amount_share_for_alpha(session, sample_sale_records):
    """Alpha total=1800000 out of grand total=2700000 → share=66.67%."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_top_products(today - timedelta(days=30), today)

    alpha = next(p for p in result.products if p.product_name == "Product Alpha")
    assert alpha.amount_share_pct == Decimal("66.67")


@pytest.mark.asyncio
async def test_top_products_limit_respected(session, sample_sale_records):
    """limit=2 should return at most 2 products."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_top_products(today - timedelta(days=30), today, limit=2)

    assert len(result.products) <= 2


@pytest.mark.asyncio
async def test_sales_breakdown_empty_returns_empty(session):
    """No data → empty groups, zero totals."""
    today = date.today()
    service = FinanceManagerDashboardService(db=session)
    result = await service.get_sales_breakdown(today - timedelta(days=30), today, GroupByType.channel)

    assert result.groups == []
    assert result.total_amount == Decimal("0.00")
