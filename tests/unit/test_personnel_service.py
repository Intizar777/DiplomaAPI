"""
Unit tests for PersonnelService.

Tests use real Postgres via testcontainers session fixture.
Gateway client is mocked or set to None for query-only tests.
"""
import pytest
from uuid import uuid4

from app.models.personnel import Location, Department, Position, Employee, ProductionLine, Workstation
from app.services.personnel_service import PersonnelService


@pytest.mark.asyncio
async def test_get_departments_returns_all(session, sample_departments):
    """Should return all departments when no filter applied."""
    service = PersonnelService(session, gateway=None)
    result = await service.get_departments()
    assert len(result) == len(sample_departments)


@pytest.mark.asyncio
async def test_get_departments_filter_by_type(session, sample_departments):
    """Should filter departments by type."""
    target_type = sample_departments[0].type
    service = PersonnelService(session, gateway=None)
    result = await service.get_departments(type=target_type)
    assert all(d.type == target_type for d in result)


@pytest.mark.asyncio
async def test_get_positions_filter_by_department(session, sample_positions, sample_departments):
    """Should filter positions by department_id."""
    target_dept_id = str(sample_departments[0].id)
    service = PersonnelService(session, gateway=None)
    result = await service.get_positions(department_id=target_dept_id)
    assert all(str(p.department_id) == target_dept_id for p in result)


@pytest.mark.asyncio
async def test_get_employees_filter_by_status(session, sample_employees):
    """Should filter employees by status."""
    target_status = sample_employees[0].status
    service = PersonnelService(session, gateway=None)
    result = await service.get_employees(status=target_status)
    assert all(e.status == target_status for e in result)


@pytest.mark.asyncio
async def test_get_locations_filter_by_type(session, sample_locations):
    """Should filter locations by type."""
    target_type = sample_locations[0].type
    service = PersonnelService(session, gateway=None)
    result = await service.get_locations(type=target_type)
    assert all(loc.type == target_type for loc in result)


@pytest.mark.asyncio
async def test_get_summary_returns_counts(session, sample_locations, sample_departments, sample_positions, sample_employees):
    """Summary should reflect inserted counts."""
    service = PersonnelService(session, gateway=None)
    summary = await service.get_summary()
    assert summary["locations"] == len(sample_locations)
    assert summary["departments"] == len(sample_departments)
    assert summary["positions"] == len(sample_positions)
    assert summary["employees"] == len(sample_employees)


@pytest.mark.asyncio
async def test_sync_from_gateway_upserts_correctly(session):
    """Mock gateway should insert once and update on second sync."""
    from unittest.mock import AsyncMock

    raw_id = str(uuid4())
    mock_gateway = AsyncMock()
    mock_gateway.get_personnel_locations = AsyncMock(return_value={
        "locations": [{"id": raw_id, "name": "Old Name", "code": "LOC-1", "type": "Plant"}]
    })
    mock_gateway.get_personnel_production_lines = AsyncMock(return_value={"productionLines": []})
    mock_gateway.get_personnel_departments = AsyncMock(return_value={"departments": []})
    mock_gateway.get_personnel_positions = AsyncMock(return_value={"positions": []})
    mock_gateway.get_personnel_workstations = AsyncMock(return_value={"workstations": []})
    mock_gateway.get_personnel_employees = AsyncMock(return_value={"employees": []})

    service = PersonnelService(session, gateway=mock_gateway)

    # First sync — insert
    count1 = await service.sync_from_gateway()
    assert count1 == 1

    loc = await session.get(Location, raw_id)
    assert loc.name == "Old Name"

    # Second sync — update
    mock_gateway.get_personnel_locations = AsyncMock(return_value={
        "locations": [{"id": raw_id, "name": "New Name", "code": "LOC-1", "type": "Plant"}]
    })
    count2 = await service.sync_from_gateway()
    assert count2 == 1

    await session.refresh(loc)
    assert loc.name == "New Name"
