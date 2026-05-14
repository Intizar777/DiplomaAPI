"""Integration tests for Products API endpoints."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio

from app.models.inventory import InventorySnapshot
from app.models.product import Product
from app.models.reference import Warehouse


@pytest_asyncio.fixture
async def sample_products(session):
    """Insert products and inventory snapshots for include tests."""
    source_id = uuid.uuid4()
    product = Product(
        id=uuid.uuid4(),
        source_system_id=str(source_id),
        code="PRD-001",
        name="Sunflower Oil",
        category="Oil",
        brand="EFKO",
        requires_quality_check=True,
    )
    warehouse = Warehouse(
        id=uuid.uuid4(),
        code="WH-01",
        name="Warehouse 1",
        location="Plant 1",
        capacity=Decimal("10000"),
        is_active=True,
    )
    snapshot = InventorySnapshot(
        product_id=source_id,
        product_name="Sunflower Oil",
        warehouse_id=warehouse.id,
        lot_number="LOT-001",
        quantity=Decimal("250"),
        unit_of_measure="kg",
        snapshot_date=date.today(),
    )
    session.add_all([product, warehouse])
    await session.flush()
    session.add(snapshot)
    await session.commit()
    return {"product_id": str(product.id)}


@pytest.mark.asyncio
async def test_products_list_include_inventory_summary(client, sample_products):
    """GET /api/v1/products include inventory summary."""
    response = await client.get("/api/v1/products", params={"include": "inventorySummary"})
    assert response.status_code == 200
    data = response.json()
    assert data["items"]
    assert data["items"][0]["inventory_summary"] is not None


@pytest.mark.asyncio
async def test_product_detail_include_inventory_summary(client, sample_products):
    """GET /api/v1/products/{id} include inventory summary."""
    response = await client.get(
        f"/api/v1/products/{sample_products['product_id']}",
        params={"include": "inventorySummary"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inventory_summary"] is not None
    assert data["inventory_summary"]["total_quantity"] == 250.0
