"""
Integration tests for Personnel API routes.

Tests use httpx.AsyncClient against real Postgres via testcontainers.
"""
import pytest


@pytest.mark.asyncio
async def test_get_departments_returns_200(client, sample_departments):
    """GET /api/v1/personnel/departments should return 200."""
    response = await client.get("/api/v1/personnel/departments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(sample_departments)


@pytest.mark.asyncio
async def test_get_departments_filter_by_type(client, sample_departments):
    """GET /api/v1/personnel/departments?type= should filter correctly."""
    target_type = sample_departments[0].type
    response = await client.get(f"/api/v1/personnel/departments?type={target_type}")
    assert response.status_code == 200
    data = response.json()
    assert all(d["type"] == target_type for d in data)


@pytest.mark.asyncio
async def test_get_positions_returns_200(client, sample_positions):
    """GET /api/v1/personnel/positions should return 200."""
    response = await client.get("/api/v1/personnel/positions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(sample_positions)


@pytest.mark.asyncio
async def test_get_employees_returns_200(client, sample_employees):
    """GET /api/v1/personnel/employees should return 200."""
    response = await client.get("/api/v1/personnel/employees")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(sample_employees)


@pytest.mark.asyncio
async def test_get_locations_returns_200(client, sample_locations):
    """GET /api/v1/personnel/locations should return 200."""
    response = await client.get("/api/v1/personnel/locations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(sample_locations)


@pytest.mark.asyncio
async def test_get_summary_returns_counts(client, sample_locations, sample_departments, sample_positions, sample_employees):
    """GET /api/v1/personnel/summary should return correct counts."""
    response = await client.get("/api/v1/personnel/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["locations"] == len(sample_locations)
    assert data["departments"] == len(sample_departments)
    assert data["positions"] == len(sample_positions)
    assert data["employees"] == len(sample_employees)


@pytest.mark.asyncio
async def test_empty_tables_return_empty_lists(client):
    """When tables are empty, endpoints should return empty lists."""
    response = await client.get("/api/v1/personnel/departments")
    assert response.status_code == 200
    assert response.json() == []

    response = await client.get("/api/v1/personnel/positions")
    assert response.status_code == 200
    assert response.json() == []

    response = await client.get("/api/v1/personnel/employees")
    assert response.status_code == 200
    assert response.json() == []

    response = await client.get("/api/v1/personnel/locations")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_unknown_filter_type_returns_empty(client):
    """Filtering by non-existent type should return empty list."""
    response = await client.get("/api/v1/personnel/locations?type=NonExistent")
    assert response.status_code == 200
    assert response.json() == []

    response = await client.get("/api/v1/personnel/departments?type=NonExistent")
    assert response.status_code == 200
    assert response.json() == []
