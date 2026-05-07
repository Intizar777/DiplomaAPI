"""
Integration tests for Output API endpoints.

Tests full request-response cycles with real database.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
import pytest_asyncio

from app.models.output import ProductionOutput


@pytest_asyncio.fixture
async def sample_outputs(session):
    """Insert production output records for testing."""
    today = date.today()
    product_id = uuid.uuid4()
    order_id = uuid.uuid4()

    outputs = [
        ProductionOutput(
            order_id=order_id,
            product_id=product_id,
            product_name="Product X",
            lot_number="LOT-OUT-001",
            quantity=Decimal("100"),
            quality_status="approved",
            production_date=today - timedelta(days=3),
            shift="morning",
            snapshot_date=today,
        ),
        ProductionOutput(
            order_id=order_id,
            product_id=product_id,
            product_name="Product X",
            lot_number="LOT-OUT-002",
            quantity=Decimal("80"),
            quality_status="rejected",
            production_date=today - timedelta(days=3),
            shift="evening",
            snapshot_date=today,
        ),
        ProductionOutput(
            order_id=order_id,
            product_id=product_id,
            product_name="Product X",
            lot_number="LOT-OUT-003",
            quantity=Decimal("120"),
            quality_status="approved",
            production_date=today - timedelta(days=2),
            shift="morning",
            snapshot_date=today,
        ),
        ProductionOutput(
            order_id=order_id,
            product_id=product_id,
            product_name="Product X",
            lot_number="LOT-OUT-004",
            quantity=Decimal("90"),
            quality_status="approved",
            production_date=today - timedelta(days=1),
            shift="night",
            snapshot_date=today,
        ),
    ]
    session.add_all(outputs)
    await session.commit()
    return outputs


@pytest.mark.asyncio
async def test_output_summary_success(client, sample_outputs):
    """Test GET /api/v1/output/summary returns aggregated output."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=10)),
        "date_to": str(today),
        "group_by": "day",
    }

    response = await client.get("/api/v1/output/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "period_from" in data
    assert "period_to" in data
    assert "group_by" in data
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_output_summary_aggregates_by_day(client, sample_outputs):
    """Test that output is correctly aggregated by day."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=10)),
        "date_to": str(today),
        "group_by": "day",
    }

    response = await client.get("/api/v1/output/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    items = data["items"]

    # Day 3 days ago has 2 lots: 100 + 80 = 180
    day3_ago = str(today - timedelta(days=3))
    day3_item = next((i for i in items if str(i["date"]) == day3_ago), None)
    assert day3_item is not None
    assert day3_item["lot_count"] == 2
    assert Decimal(str(day3_item["total_quantity"])) == Decimal("180")


@pytest.mark.asyncio
async def test_output_summary_approved_count(client, sample_outputs):
    """Test that approved_count is tracked correctly."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=10)),
        "date_to": str(today),
        "group_by": "day",
    }

    response = await client.get("/api/v1/output/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    items = {str(i["date"]): i for i in data["items"]}

    day3_ago = str(today - timedelta(days=3))
    # Only 1 approved on day3
    assert items[day3_ago]["approved_count"] == 1


@pytest.mark.asyncio
async def test_output_summary_group_by_shift(client, sample_outputs):
    """Test output aggregated by shift."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=10)),
        "date_to": str(today),
        "group_by": "shift",
    }

    response = await client.get("/api/v1/output/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["group_by"] == "shift"
    assert len(data["items"]) > 0
    # Each item should have a shift value
    for item in data["items"]:
        assert item.get("shift") is not None or item.get("date") is not None


@pytest.mark.asyncio
async def test_output_summary_empty_for_future_dates(client):
    """Test empty result for future date range."""
    future = date.today() + timedelta(days=100)
    params = {
        "date_from": str(future),
        "date_to": str(future + timedelta(days=7)),
        "group_by": "day",
    }

    response = await client.get("/api/v1/output/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []


@pytest.mark.asyncio
async def test_output_by_shift_success(client, sample_outputs):
    """Test GET /api/v1/output/by-shift returns shift breakdown."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=10)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/output/by-shift", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "period_from" in data
    assert "period_to" in data
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_output_by_shift_contains_correct_fields(client, sample_outputs):
    """Test that by-shift response contains required fields per item."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=10)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/output/by-shift", params=params)

    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert "date" in item
        assert "shift" in item
        assert "total_quantity" in item
        assert "lot_count" in item


@pytest.mark.asyncio
async def test_output_by_shift_ordered_by_date(client, sample_outputs):
    """Test that by-shift items are returned in chronological order."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=10)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/output/by-shift", params=params)

    assert response.status_code == 200
    data = response.json()
    dates = [item["date"] for item in data["items"]]
    assert dates == sorted(dates)


@pytest.mark.asyncio
async def test_output_by_shift_empty_for_future_dates(client):
    """Test empty result for future date range."""
    future = date.today() + timedelta(days=100)
    params = {
        "date_from": str(future),
        "date_to": str(future + timedelta(days=7)),
    }

    response = await client.get("/api/v1/output/by-shift", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
