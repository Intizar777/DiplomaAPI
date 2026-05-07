"""
Integration tests for Sales API endpoints.

Tests full request-response cycles with real database.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
import pytest_asyncio

from app.models.sales import AggregatedSales, SalesTrends, SaleRecord


@pytest_asyncio.fixture
async def sample_aggregated_sales(session):
    """Insert aggregated sales data for summary endpoint tests."""
    today = date.today()
    from_date = today - timedelta(days=30)

    records = [
        AggregatedSales(
            period_from=from_date,
            period_to=today,
            group_by_type="region",
            group_key="North",
            total_quantity=Decimal("500"),
            total_amount=Decimal("50000"),
            sales_count=25,
            avg_order_value=Decimal("2000"),
        ),
        AggregatedSales(
            period_from=from_date,
            period_to=today,
            group_by_type="region",
            group_key="South",
            total_quantity=Decimal("300"),
            total_amount=Decimal("30000"),
            sales_count=15,
            avg_order_value=Decimal("2000"),
        ),
        AggregatedSales(
            period_from=from_date,
            period_to=today,
            group_by_type="channel",
            group_key="online",
            total_quantity=Decimal("200"),
            total_amount=Decimal("20000"),
            sales_count=10,
            avg_order_value=Decimal("2000"),
        ),
    ]
    session.add_all(records)
    await session.commit()
    return records


@pytest_asyncio.fixture
async def sample_trends(session):
    """Insert sales trends data."""
    today = date.today()
    trends = []
    for i in range(5):
        trends.append(
            SalesTrends(
                trend_date=today - timedelta(days=i),
                interval_type="day",
                region=None,
                channel=None,
                total_amount=Decimal(str(1000 * (i + 1))),
                total_quantity=Decimal(str(100 * (i + 1))),
                order_count=5 * (i + 1),
            )
        )
    session.add_all(trends)
    await session.commit()
    return trends


@pytest_asyncio.fixture
async def sample_sale_records(session):
    """Insert raw sale records for top-products and regions tests."""
    today = date.today()
    product_a = uuid.uuid4()
    product_b = uuid.uuid4()

    records = [
        SaleRecord(
            external_id="ext-001",
            product_id=product_a,
            product_name="Product A",
            customer_name="Customer X",
            quantity=Decimal("10"),
            amount=Decimal("5000"),
            sale_date=today - timedelta(days=5),
            region="East",
            channel="online",
            snapshot_date=today,
        ),
        SaleRecord(
            external_id="ext-002",
            product_id=product_b,
            product_name="Product B",
            customer_name="Customer Y",
            quantity=Decimal("20"),
            amount=Decimal("3000"),
            sale_date=today - timedelta(days=3),
            region="West",
            channel="retail",
            snapshot_date=today,
        ),
        SaleRecord(
            external_id="ext-003",
            product_id=product_a,
            product_name="Product A",
            customer_name="Customer Z",
            quantity=Decimal("5"),
            amount=Decimal("2500"),
            sale_date=today - timedelta(days=1),
            region="East",
            channel="online",
            snapshot_date=today,
        ),
    ]
    session.add_all(records)
    await session.commit()
    return {"product_a": product_a, "product_b": product_b, "records": records}


@pytest.mark.asyncio
async def test_sales_summary_success(client, sample_aggregated_sales):
    """Test GET /api/v1/sales/summary returns grouped summary."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "group_by": "region",
    }

    response = await client.get("/api/v1/sales/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "total_amount" in data
    assert "period_from" in data
    assert "period_to" in data
    assert data["group_by"] == "region"
    assert len(data["summary"]) > 0


@pytest.mark.asyncio
async def test_sales_summary_groups_correctly(client, sample_aggregated_sales):
    """Test that summary returns correct totals per group."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "group_by": "region",
    }

    response = await client.get("/api/v1/sales/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    regions = {item["group_key"]: item for item in data["summary"]}
    assert "North" in regions
    assert Decimal(str(regions["North"]["total_amount"])) == Decimal("50000")
    assert Decimal(str(data["total_amount"])) == Decimal("80000")


@pytest.mark.asyncio
async def test_sales_summary_empty_for_future_dates(client):
    """Test summary returns empty list for future date ranges."""
    future = date.today() + timedelta(days=100)
    params = {
        "date_from": str(future),
        "date_to": str(future + timedelta(days=30)),
        "group_by": "region",
    }

    response = await client.get("/api/v1/sales/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == []
    assert Decimal(str(data["total_amount"])) == Decimal("0")


@pytest.mark.asyncio
async def test_sales_summary_group_by_channel(client, sample_aggregated_sales):
    """Test summary filtered by channel group."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "group_by": "channel",
    }

    response = await client.get("/api/v1/sales/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["group_by"] == "channel"
    assert any(item["group_key"] == "online" for item in data["summary"])


@pytest.mark.asyncio
async def test_sales_trends_success(client, sample_trends):
    """Test GET /api/v1/sales/trends returns trend data."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=10)),
        "date_to": str(today),
        "interval": "day",
    }

    response = await client.get("/api/v1/sales/trends", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert "interval" in data
    assert "period_from" in data
    assert len(data["trends"]) > 0


@pytest.mark.asyncio
async def test_sales_trends_ordered_by_date(client, sample_trends):
    """Test that trends are returned in chronological order."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=10)),
        "date_to": str(today),
        "interval": "day",
    }

    response = await client.get("/api/v1/sales/trends", params=params)

    assert response.status_code == 200
    data = response.json()
    trend_dates = [item["trend_date"] for item in data["trends"]]
    assert trend_dates == sorted(trend_dates)


@pytest.mark.asyncio
async def test_sales_trends_empty_for_future_dates(client):
    """Test trends returns empty list for future dates."""
    future = date.today() + timedelta(days=100)
    params = {
        "date_from": str(future),
        "date_to": str(future + timedelta(days=30)),
        "interval": "day",
    }

    response = await client.get("/api/v1/sales/trends", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["trends"] == []


@pytest.mark.asyncio
async def test_sales_top_products_success(client, sample_sale_records):
    """Test GET /api/v1/sales/top-products returns top products."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "limit": 10,
    }

    response = await client.get("/api/v1/sales/top-products", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "period_from" in data
    assert "limit" in data
    assert len(data["products"]) > 0


@pytest.mark.asyncio
async def test_sales_top_products_ordered_by_revenue(client, sample_sale_records):
    """Test that top products are ordered by total_amount descending."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "limit": 10,
    }

    response = await client.get("/api/v1/sales/top-products", params=params)

    assert response.status_code == 200
    data = response.json()
    products = data["products"]
    if len(products) > 1:
        amounts = [Decimal(str(p["total_amount"])) for p in products]
        assert amounts == sorted(amounts, reverse=True)


@pytest.mark.asyncio
async def test_sales_top_products_respects_limit(client, sample_sale_records):
    """Test that limit parameter is respected."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "limit": 1,
    }

    response = await client.get("/api/v1/sales/top-products", params=params)

    assert response.status_code == 200
    data = response.json()
    assert len(data["products"]) <= 1
    assert data["limit"] == 1


@pytest.mark.asyncio
async def test_sales_regions_success(client, sample_sale_records):
    """Test GET /api/v1/sales/regions returns regional breakdown."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/sales/regions", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "regions" in data
    assert "period_from" in data
    assert "period_to" in data


@pytest.mark.asyncio
async def test_sales_regions_percentages_sum_to_100(client, sample_sale_records):
    """Test that region percentages sum to 100."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/sales/regions", params=params)

    assert response.status_code == 200
    data = response.json()
    regions = data["regions"]
    if regions:
        total_pct = sum(Decimal(str(r["percentage"])) for r in regions)
        assert abs(total_pct - Decimal("100")) < Decimal("0.1")
