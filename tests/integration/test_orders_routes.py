"""
Integration tests for Orders API endpoints.

Tests full request-response cycles with real database.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest
import pytest_asyncio

from app.models.orders import OrderSnapshot


@pytest_asyncio.fixture
async def sample_orders(session):
    """Insert sample order snapshots for testing."""
    today = date.today()
    product_id = uuid.uuid4()
    order_ids = [uuid.uuid4() for _ in range(5)]

    orders = [
        OrderSnapshot(
            order_id=order_ids[0],
            external_order_id="EXT-001",
            product_id=product_id,
            product_name="Widget A",
            target_quantity=Decimal("100"),
            actual_quantity=Decimal("95"),
            unit_of_measure="pcs",
            status="completed",
            production_line="Line-1",
            planned_start=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
            planned_end=datetime(2026, 1, 1, 16, 0, tzinfo=timezone.utc),
            actual_start=datetime(2026, 1, 1, 8, 5, tzinfo=timezone.utc),
            actual_end=datetime(2026, 1, 1, 16, 10, tzinfo=timezone.utc),
            snapshot_date=today - timedelta(days=5),
        ),
        OrderSnapshot(
            order_id=order_ids[1],
            external_order_id="EXT-002",
            product_id=product_id,
            product_name="Widget B",
            target_quantity=Decimal("200"),
            actual_quantity=None,
            unit_of_measure="pcs",
            status="in_progress",
            production_line="Line-1",
            planned_start=datetime(2026, 1, 2, 8, 0, tzinfo=timezone.utc),
            planned_end=datetime(2026, 1, 2, 16, 0, tzinfo=timezone.utc),
            actual_start=datetime(2026, 1, 2, 8, 0, tzinfo=timezone.utc),
            actual_end=None,
            snapshot_date=today - timedelta(days=2),
        ),
        OrderSnapshot(
            order_id=order_ids[2],
            external_order_id="EXT-003",
            product_id=product_id,
            product_name="Widget C",
            target_quantity=Decimal("50"),
            actual_quantity=None,
            unit_of_measure="pcs",
            status="planned",
            production_line="Line-2",
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            snapshot_date=today - timedelta(days=1),
        ),
        OrderSnapshot(
            order_id=order_ids[3],
            external_order_id="EXT-004",
            product_id=product_id,
            product_name="Widget D",
            target_quantity=Decimal("150"),
            actual_quantity=Decimal("0"),
            unit_of_measure="pcs",
            status="cancelled",
            production_line="Line-2",
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            snapshot_date=today - timedelta(days=3),
        ),
        OrderSnapshot(
            order_id=order_ids[4],
            external_order_id="EXT-005",
            product_id=product_id,
            product_name="Widget E",
            target_quantity=Decimal("75"),
            actual_quantity=Decimal("75"),
            unit_of_measure="pcs",
            status="completed",
            production_line="Line-1",
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            snapshot_date=today - timedelta(days=1),
        ),
    ]
    session.add_all(orders)
    await session.commit()
    return {"orders": orders, "order_ids": order_ids, "product_id": product_id}


@pytest.mark.asyncio
async def test_order_status_summary_success(client, sample_orders):
    """Test GET /api/v1/orders/status-summary returns status breakdown."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/orders/status-summary", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "by_status" in data
    assert "by_production_line" in data
    assert "period_from" in data
    assert "period_to" in data


@pytest.mark.asyncio
async def test_order_status_summary_counts(client, sample_orders):
    """Test that status counts match inserted data."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/orders/status-summary", params=params)

    assert response.status_code == 200
    data = response.json()
    by_status = data["by_status"]
    assert by_status["completed"] == 2
    assert by_status["in_progress"] == 1
    assert by_status["planned"] == 1
    assert by_status["cancelled"] == 1


@pytest.mark.asyncio
async def test_order_status_summary_by_production_line(client, sample_orders):
    """Test that status summary breaks down by production line."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/orders/status-summary", params=params)

    assert response.status_code == 200
    data = response.json()
    by_line = data["by_production_line"]
    assert "Line-1" in by_line
    assert "Line-2" in by_line
    assert by_line["Line-1"]["completed"] == 2
    assert by_line["Line-2"]["planned"] == 1


@pytest.mark.asyncio
async def test_order_status_summary_filter_by_line(client, sample_orders):
    """Test filtering by production_line."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "production_line": "Line-1",
    }

    response = await client.get("/api/v1/orders/status-summary", params=params)

    assert response.status_code == 200
    data = response.json()
    by_status = data["by_status"]
    # Only Line-1 orders: 2 completed, 1 in_progress
    assert by_status["completed"] == 2
    assert by_status["in_progress"] == 1
    assert by_status["planned"] == 0


@pytest.mark.asyncio
async def test_order_status_summary_empty_for_future_dates(client):
    """Test empty result for future date range."""
    future = date.today() + timedelta(days=100)
    params = {
        "date_from": str(future),
        "date_to": str(future + timedelta(days=30)),
    }

    response = await client.get("/api/v1/orders/status-summary", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["by_status"]["planned"] == 0
    assert data["by_production_line"] == {}


@pytest.mark.asyncio
async def test_orders_list_success(client, sample_orders):
    """Test GET /api/v1/orders/list returns paginated orders."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/orders/list", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "pages" in data
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_orders_list_filter_by_status(client, sample_orders):
    """Test filtering orders by status."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "status": "completed",
    }

    response = await client.get("/api/v1/orders/list", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for order in data["orders"]:
        assert order["status"] == "completed"


@pytest.mark.asyncio
async def test_orders_list_filter_by_production_line(client, sample_orders):
    """Test filtering orders by production_line."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "production_line": "Line-2",
    }

    response = await client.get("/api/v1/orders/list", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for order in data["orders"]:
        assert order["production_line"] == "Line-2"


@pytest.mark.asyncio
async def test_orders_list_pagination(client, sample_orders):
    """Test pagination parameters."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "page": 1,
        "limit": 2,
    }

    response = await client.get("/api/v1/orders/list", params=params)

    assert response.status_code == 200
    data = response.json()
    assert len(data["orders"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["pages"] == 3  # 5 orders, limit 2 → 3 pages


@pytest.mark.asyncio
async def test_order_detail_success(client, sample_orders):
    """Test GET /api/v1/orders/{order_id} returns order detail."""
    order_id = str(sample_orders["order_ids"][0])

    response = await client.get(f"/api/v1/orders/{order_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == order_id
    assert data["status"] == "completed"
    assert data["product_name"] == "Widget A"
    assert "outputs" in data


@pytest.mark.asyncio
async def test_order_detail_not_found(client):
    """Test that non-existent order returns 404."""
    fake_id = str(uuid.uuid4())

    response = await client.get(f"/api/v1/orders/{fake_id}")

    assert response.status_code == 404
