"""
Integration tests for GET /api/production/production-lines.

Verifies that the route continues to work identically after the Phase 6
service-layer extraction (production_analytics.py no longer queries DB directly).
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProductionLine


@pytest_asyncio.fixture
async def active_lines(session: AsyncSession):
    lines = [
        ProductionLine(name="Line One", code="L-1", division="Pressing", is_active=True, description="First line"),
        ProductionLine(name="Line Two", code="L-2", division="Refining", is_active=True, description=None),
        ProductionLine(name="Line Three", code="L-3", division="Pressing", is_active=False, description=None),
    ]
    session.add_all(lines)
    await session.commit()
    return lines


@pytest.mark.asyncio
async def test_list_production_lines_returns_200(client: AsyncClient, active_lines):
    response = await client.get("/api/production/production-lines")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_production_lines_shape(client: AsyncClient, active_lines):
    response = await client.get("/api/production/production-lines")
    data = response.json()
    assert "production_lines" in data
    assert "total" in data
    assert isinstance(data["production_lines"], list)
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_list_production_lines_excludes_inactive(client: AsyncClient, active_lines):
    response = await client.get("/api/production/production-lines")
    data = response.json()
    codes = [line["code"] for line in data["production_lines"]]
    assert "L-3" not in codes
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_production_lines_division_filter(client: AsyncClient, active_lines):
    response = await client.get("/api/production/production-lines", params={"division": "Pressing"})
    data = response.json()
    assert data["total"] == 1
    assert data["production_lines"][0]["code"] == "L-1"


@pytest.mark.asyncio
async def test_list_production_lines_total_scoped_to_filter(client: AsyncClient, active_lines):
    """total must count only lines matching the division filter, not all active lines."""
    response = await client.get("/api/production/production-lines", params={"division": "Refining"})
    data = response.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_list_production_lines_pagination(client: AsyncClient, active_lines):
    response = await client.get("/api/production/production-lines", params={"limit": 1, "offset": 0})
    data = response.json()
    assert len(data["production_lines"]) == 1
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_production_lines_item_fields(client: AsyncClient, active_lines):
    response = await client.get("/api/production/production-lines")
    item = response.json()["production_lines"][0]
    assert "id" in item
    assert "code" in item
    assert "name" in item
    assert "division" in item
    assert "is_active" in item
