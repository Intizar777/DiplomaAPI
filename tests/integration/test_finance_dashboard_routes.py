"""
Integration tests for Finance Manager Dashboard HTTP endpoints.

Uses httpx AsyncClient + testcontainers PostgreSQL (real DB, full request-response cycle).
"""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

from app.models.sales import AggregatedSales, SalesTrends, SaleRecord


# ---------------------------------------------------------------------------
# Local fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sample_finance_data(session):
    """
    Insert compact dataset for Finance route integration tests.

    AggregatedSales: 2 channel groups (wholesale, retail), 2 region groups.
    SalesTrends: 2 weekly points (region=None, channel=None).
    SaleRecord: 4 records for 2 products.
    """
    today = date.today()
    period_from = today - timedelta(days=15)
    w1 = today - timedelta(days=14)
    w2 = today - timedelta(days=7)
    pid_a = uuid4()
    pid_b = uuid4()

    sales_rows = [
        AggregatedSales(
            period_from=period_from, period_to=today,
            group_by_type="channel", group_key="wholesale",
            total_quantity=Decimal("10000"), total_amount=Decimal("1000000"),
            sales_count=50,
        ),
        AggregatedSales(
            period_from=period_from, period_to=today,
            group_by_type="channel", group_key="retail",
            total_quantity=Decimal("8000"), total_amount=Decimal("800000"),
            sales_count=80,
        ),
    ]
    for r in sales_rows:
        session.add(r)

    trend_rows = [
        SalesTrends(
            trend_date=w1, interval_type="week", region=None, channel=None,
            total_amount=Decimal("500000"), total_quantity=Decimal("5000"), order_count=25,
        ),
        SalesTrends(
            trend_date=w2, interval_type="week", region=None, channel=None,
            total_amount=Decimal("600000"), total_quantity=Decimal("6000"), order_count=30,
        ),
    ]
    for r in trend_rows:
        session.add(r)

    record_rows = [
        SaleRecord(
            product_id=pid_a, product_name="Alpha",
            amount=Decimal("700000"), quantity=Decimal("7000"),
            sale_date=period_from + timedelta(days=5), snapshot_date=today,
        ),
        SaleRecord(
            product_id=pid_a, product_name="Alpha",
            amount=Decimal("300000"), quantity=Decimal("3000"),
            sale_date=period_from + timedelta(days=8), snapshot_date=today,
        ),
        SaleRecord(
            product_id=pid_b, product_name="Beta",
            amount=Decimal("400000"), quantity=Decimal("4000"),
            sale_date=period_from + timedelta(days=3), snapshot_date=today,
        ),
        SaleRecord(
            product_id=pid_b, product_name="Beta",
            amount=Decimal("200000"), quantity=Decimal("2000"),
            sale_date=period_from + timedelta(days=10), snapshot_date=today,
        ),
    ]
    for r in record_rows:
        session.add(r)

    await session.commit()
    return {"pid_a": pid_a, "pid_b": pid_b}


# ---------------------------------------------------------------------------
# Sales breakdown endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sales_breakdown_returns_200(client, sample_finance_data):
    """GET /finance/sales-breakdown returns 200 with groups key."""
    response = await client.get("/api/v1/dashboards/finance/sales-breakdown?group_by=channel")
    assert response.status_code == 200
    data = response.json()
    assert "groups" in data
    assert "total_amount" in data
    assert len(data["groups"]) >= 1


@pytest.mark.asyncio
async def test_sales_breakdown_decimal_as_string(client, sample_finance_data):
    """total_amount and avg_order_value must be serialized as strings."""
    response = await client.get("/api/v1/dashboards/finance/sales-breakdown")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["total_amount"], str)
    for group in data["groups"]:
        assert isinstance(group["total_amount"], str)
        assert isinstance(group["avg_order_value"], str)


# ---------------------------------------------------------------------------
# Revenue trend endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_revenue_trend_returns_200(client, sample_finance_data):
    """GET /finance/revenue-trend returns 200 with data key."""
    response = await client.get("/api/v1/dashboards/finance/revenue-trend?interval=week")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "interval" in data
    assert data["interval"] == "week"


@pytest.mark.asyncio
async def test_revenue_trend_mom_growth_none_for_first(client, sample_finance_data):
    """First data point must have mom_growth_pct=null."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "interval": "week",
    }
    response = await client.get("/api/v1/dashboards/finance/revenue-trend", params=params)
    assert response.status_code == 200
    data = response.json()
    if len(data["data"]) > 0:
        assert data["data"][0]["mom_growth_pct"] is None


# ---------------------------------------------------------------------------
# Top products endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_top_products_returns_200(client, sample_finance_data):
    """GET /finance/top-products returns 200 with products and total_amount keys."""
    response = await client.get("/api/v1/dashboards/finance/top-products")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "total_amount" in data
    assert "sort_by" in data


@pytest.mark.asyncio
async def test_top_products_sort_by_amount_default(client, sample_finance_data):
    """Default sort_by=amount; first product must have highest total_amount."""
    response = await client.get("/api/v1/dashboards/finance/top-products")
    assert response.status_code == 200
    data = response.json()
    if len(data["products"]) > 1:
        amounts = [float(p["total_amount"]) for p in data["products"]]
        assert amounts == sorted(amounts, reverse=True)


# ---------------------------------------------------------------------------
# Empty database tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_all_endpoints_empty_database(client):
    """All 3 endpoints return 200 with empty/zero data on empty DB."""
    resp_breakdown = await client.get("/api/v1/dashboards/finance/sales-breakdown")
    assert resp_breakdown.status_code == 200
    assert resp_breakdown.json()["groups"] == []

    resp_trend = await client.get("/api/v1/dashboards/finance/revenue-trend")
    assert resp_trend.status_code == 200
    assert resp_trend.json()["data"] == []

    resp_top = await client.get("/api/v1/dashboards/finance/top-products")
    assert resp_top.status_code == 200
    assert resp_top.json()["products"] == []
    assert float(resp_top.json()["total_amount"]) == 0
