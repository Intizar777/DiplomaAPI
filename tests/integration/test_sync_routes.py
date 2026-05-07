"""
Integration tests for Sync API routes.

Tests verify sync endpoints include personnel and return correct responses.
Database state is verified via testcontainers PostgreSQL.
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.models.personnel import Location, Department, Position, Employee
from app.services.personnel_service import PersonnelService


@pytest.mark.asyncio
async def test_sync_status_includes_personnel(client):
    """GET /api/v1/sync/status should include personnel in tasks list."""
    response = await client.get("/api/v1/sync/status")
    assert response.status_code == 200
    data = response.json()

    task_names = [t["task_name"] for t in data["tasks"]]
    assert "personnel" in task_names


@pytest.mark.asyncio
async def test_sync_trigger_all_includes_personnel(client):
    """POST /api/v1/sync/trigger should include personnel in triggered tasks."""
    response = await client.post("/api/v1/sync/trigger")
    assert response.status_code == 200
    data = response.json()

    assert "personnel" in data["triggered_tasks"]


@pytest.mark.asyncio
async def test_sync_trigger_personnel_accepted(client):
    """POST /api/v1/sync/trigger/personnel should be accepted."""
    response = await client.post("/api/v1/sync/trigger/personnel")
    assert response.status_code == 200
    data = response.json()

    assert data["triggered_tasks"] == ["personnel"]
    assert "personnel" in data["message"].lower()


@pytest.mark.asyncio
async def test_sync_trigger_invalid_task_returns_400(client):
    """POST /api/v1/sync/trigger/invalid should return 400."""
    response = await client.post("/api/v1/sync/trigger/invalid")
    assert response.status_code == 400
    data = response.json()
    assert "Invalid task" in data["detail"]


@pytest.mark.asyncio
async def test_sync_personnel_populates_database(session):
    """PersonnelService.sync_from_gateway with mock gateway should fill the DB."""
    loc_id = str(uuid4())
    dept_id = str(uuid4())
    pos_id = str(uuid4())
    emp_id = str(uuid4())

    mock_gateway = AsyncMock()
    mock_gateway.get_personnel_locations = AsyncMock(return_value={
        "locations": [{"id": loc_id, "name": "Test Plant", "code": "TP-1", "type": "Plant"}]
    })
    mock_gateway.get_personnel_production_lines = AsyncMock(return_value={"productionLines": []})
    mock_gateway.get_personnel_departments = AsyncMock(return_value={
        "departments": [{"id": dept_id, "name": "Test Dept", "code": "TD-1", "locationId": loc_id, "type": "Production"}]
    })
    mock_gateway.get_personnel_positions = AsyncMock(return_value={
        "positions": [{"id": pos_id, "name": "Test Position", "code": "TP-1", "departmentId": dept_id}]
    })
    mock_gateway.get_personnel_workstations = AsyncMock(return_value={"workstations": []})
    mock_gateway.get_personnel_employees = AsyncMock(return_value={
        "employees": [{"id": emp_id, "firstName": "John", "lastName": "Doe", "employeeNumber": "EMP-1", "positionId": pos_id, "status": "active"}]
    })

    service = PersonnelService(session, gateway=mock_gateway)
    count = await service.sync_from_gateway()

    assert count == 4  # 1 location + 1 department + 1 position + 1 employee

    # Verify data in DB
    loc = await session.get(Location, loc_id)
    assert loc is not None
    assert loc.name == "Test Plant"

    dept = await session.get(Department, dept_id)
    assert dept is not None
    assert dept.name == "Test Dept"
    assert str(dept.location_id) == loc_id

    pos = await session.get(Position, pos_id)
    assert pos is not None
    assert pos.name == "Test Position"
    assert str(pos.department_id) == dept_id

    emp = await session.get(Employee, emp_id)
    assert emp is not None
    assert emp.first_name == "John"
    assert emp.last_name == "Doe"
    assert str(emp.position_id) == pos_id
    assert emp.status == "active"
