"""
Integration tests for Inventory API endpoints.

Tests full request-response cycles with real database.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest
import pytest_asyncio

from app.models.inventory import InventorySnapshot


@pytest_asyncio.fixture
async def sample_inventory(session):
    """Insert inventory snapshot records for testing."""
    today = date.today()
    product_a = uuid.uuid4()
    product_b = uuid.uuid4()
    yesterday = today - timedelta(days=1)

    snapshots = [
        # Latest snapshot (today)
        InventorySnapshot(
            product_id=product_a,
            product_name="Widget A",
            warehouse_code="WH-01",
            lot_number="LOT-A-001",
            quantity=Decimal("500"),
            unit_of_measure="pcs",
            last_updated=datetime(2026, 5, 7, 10, 0, tzinfo=timezone.utc),
            snapshot_date=today,
        ),
        InventorySnapshot(
            product_id=product_a,
            product_name="Widget A",
            warehouse_code="WH-02",
            lot_number="LOT-A-002",
            quantity=Decimal("300"),
            unit_of_measure="pcs",
            last_updated=datetime(2026, 5, 7, 10, 0, tzinfo=timezone.utc),
            snapshot_date=today,
        ),
        InventorySnapshot(
            product_id=product_b,
            product_name="Widget B",
            warehouse_code="WH-01",
            lot_number="LOT-B-001",
            quantity=Decimal("200"),
            unit_of_measure="kg",
            last_updated=datetime(2026, 5, 7, 10, 0, tzinfo=timezone.utc),
            snapshot_date=today,
        ),
        # Older snapshot (yesterday) — should not appear in /current
        InventorySnapshot(
            product_id=product_a,
            product_name="Widget A",
            warehouse_code="WH-01",
            lot_number="LOT-A-OLD",
            quantity=Decimal("600"),
            unit_of_measure="pcs",
            last_updated=datetime(2026, 5, 6, 10, 0, tzinfo=timezone.utc),
            snapshot_date=yesterday,
        ),
    ]
    session.add_all(snapshots)
    await session.commit()
    return {"product_a": product_a, "product_b": product_b}


@pytest.mark.asyncio
async def test_inventory_current_success(client, sample_inventory):
    """Test GET /api/v1/inventory/current returns latest snapshot."""
    response = await client.get("/api/v1/inventory/current")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "snapshot_date" in data
    assert len(data["items"]) == 3  # only latest snapshot (today)


@pytest.mark.asyncio
async def test_inventory_current_returns_latest_only(client, sample_inventory):
    """Test that /current only returns records from the latest snapshot_date."""
    today = date.today()

    response = await client.get("/api/v1/inventory/current")

    assert response.status_code == 200
    data = response.json()
    assert data["snapshot_date"] == str(today)
    for item in data["items"]:
        # Verify no old lot numbers are returned
        assert item.get("lot_number") != "LOT-A-OLD"


@pytest.mark.asyncio
async def test_inventory_current_filter_by_warehouse(client, sample_inventory):
    """Test filtering current inventory by warehouse_code."""
    response = await client.get(
        "/api/v1/inventory/current", params={"warehouse_code": "WH-01"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2  # Widget A + Widget B in WH-01
    for item in data["items"]:
        assert item["warehouse_code"] == "WH-01"


@pytest.mark.asyncio
async def test_inventory_current_filter_by_product(client, sample_inventory):
    """Test filtering current inventory by product_id."""
    product_a = str(sample_inventory["product_a"])

    response = await client.get(
        "/api/v1/inventory/current", params={"product_id": product_a}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2  # Widget A in WH-01 and WH-02
    for item in data["items"]:
        assert item["product_id"] == product_a


@pytest.mark.asyncio
async def test_inventory_current_empty_database(client):
    """Test that empty database returns empty items list."""
    response = await client.get("/api/v1/inventory/current")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["snapshot_date"] is None


@pytest.mark.asyncio
async def test_inventory_current_item_fields(client, sample_inventory):
    """Test that inventory items contain required fields."""
    response = await client.get(
        "/api/v1/inventory/current", params={"warehouse_code": "WH-01"}
    )

    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert "product_id" in item
        assert "warehouse_code" in item
        assert "quantity" in item
        assert "unit_of_measure" in item


@pytest.mark.asyncio
async def test_inventory_trends_success(client, sample_inventory):
    """Test GET /api/v1/inventory/trends returns trend data for a product."""
    today = date.today()
    product_a = str(sample_inventory["product_a"])
    params = {
        "product_id": product_a,
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/inventory/trends", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "product_id" in data
    assert data["product_id"] == product_a
    assert len(data["items"]) == 2  # today + yesterday snapshots
    for item in data["items"]:
        assert "date" in item
        assert "total_quantity" in item
        assert item["total_quantity"] > 0


@pytest.mark.asyncio
async def test_inventory_trends_requires_product_id(client):
    """Test that missing product_id returns 422 validation error."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/inventory/trends", params=params)

    assert response.status_code == 422
