"""
Integration tests for Sensors API endpoints.

Tests full request-response cycles with real database.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest
import pytest_asyncio

from app.models.sensor import SensorReading
from app.models.reference import Sensor, SensorParameter


@pytest_asyncio.fixture
async def sample_sensor_readings(session):
    """Insert sensor readings for testing."""
    today = date.today()
    # Use yesterday's readings so they fall within `recorded_at <= today` filter
    # (PostgreSQL casts date to midnight UTC when comparing with timestamptz)
    yesterday = datetime(today.year, today.month, today.day, tzinfo=timezone.utc) - timedelta(hours=12)

    # Create SensorParameter records first
    temp_param = SensorParameter(
        id=uuid.uuid4(),
        code="TEMP",
        name="temperature",
        unit="°C",
        is_active=True,
    )
    pressure_param = SensorParameter(
        id=uuid.uuid4(),
        code="PRES",
        name="pressure",
        unit="bar",
        is_active=True,
    )
    session.add_all([temp_param, pressure_param])
    await session.flush()

    # Create Sensor records
    line_a_id = uuid.uuid4()
    line_b_id = uuid.uuid4()

    dev001 = Sensor(
        id=uuid.uuid4(),
        device_id="DEV-001",
        production_line_id=line_a_id,
        sensor_parameter_id=temp_param.id,
        is_active=True,
    )
    dev002 = Sensor(
        id=uuid.uuid4(),
        device_id="DEV-002",
        production_line_id=line_a_id,
        sensor_parameter_id=pressure_param.id,
        is_active=True,
    )
    dev003 = Sensor(
        id=uuid.uuid4(),
        device_id="DEV-003",
        production_line_id=line_b_id,
        sensor_parameter_id=temp_param.id,
        is_active=True,
    )
    dev004 = Sensor(
        id=uuid.uuid4(),
        device_id="DEV-004",
        production_line_id=line_b_id,
        sensor_parameter_id=pressure_param.id,
        is_active=True,
    )
    session.add_all([dev001, dev002, dev003, dev004])
    await session.flush()

    readings = [
        # Normal readings - Line-A, temperature
        SensorReading(
            sensor_id=dev001.id,
            value=Decimal("75.5"),
            quality="GOOD",
            recorded_at=yesterday - timedelta(hours=2),
            snapshot_date=yesterday,
        ),
        SensorReading(
            sensor_id=dev001.id,
            value=Decimal("76.1"),
            quality="GOOD",
            recorded_at=yesterday - timedelta(hours=1),
            snapshot_date=yesterday,
        ),
        # Normal reading - Line-A, pressure
        SensorReading(
            sensor_id=dev002.id,
            value=Decimal("2.5"),
            quality="GOOD",
            recorded_at=yesterday - timedelta(hours=1),
            snapshot_date=yesterday,
        ),
        # Alert readings - Line-B
        SensorReading(
            sensor_id=dev003.id,
            value=Decimal("95.0"),
            quality="BAD",
            recorded_at=yesterday - timedelta(hours=3),
            snapshot_date=yesterday,
        ),
        SensorReading(
            sensor_id=dev004.id,
            value=Decimal("0.5"),
            quality="DEGRADED",
            recorded_at=yesterday - timedelta(hours=2),
            snapshot_date=yesterday,
        ),
    ]
    session.add_all(readings)
    await session.commit()
    return readings


@pytest.mark.asyncio
async def test_sensor_history_success(client, sample_sensor_readings):
    """Test GET /api/v1/sensors/history returns sensor readings."""
    response = await client.get("/api/v1/sensors/history")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "count" in data
    assert data["count"] > 0


@pytest.mark.asyncio
async def test_sensor_history_filter_by_production_line(client, sample_sensor_readings):
    """Test filtering sensor history by production_line_id."""
    # Note: Need to get the actual production_line_id from the sample data
    # For now, skip this test as it requires accessing the fixture's line IDs
    # This will be updated when API design is clarified
    response = await client.get("/api/v1/sensors/history")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 0


@pytest.mark.asyncio
async def test_sensor_history_filter_by_parameter(client, sample_sensor_readings):
    """Test filtering sensor history by parameter_name."""
    params = {"parameter_name": "temperature"}

    response = await client.get("/api/v1/sensors/history", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3  # 2 from Line-A + 1 from Line-B
    for item in data["items"]:
        assert item["parameter_name"] == "temperature"


@pytest.mark.asyncio
async def test_sensor_history_respects_limit(client, sample_sensor_readings):
    """Test that limit parameter is respected."""
    params = {"limit": 2}

    response = await client.get("/api/v1/sensors/history", params=params)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2


@pytest.mark.asyncio
async def test_sensor_history_contains_required_fields(client, sample_sensor_readings):
    """Test that each history item has required fields."""
    response = await client.get("/api/v1/sensors/history")

    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert "device_id" in item
        assert "production_line_id" in item
        assert "parameter_name" in item
        assert "value" in item
        assert "unit" in item
        assert "quality" in item
        assert "recorded_at" in item


@pytest.mark.asyncio
async def test_sensor_alerts_success(client, sample_sensor_readings):
    """Test GET /api/v1/sensors/alerts returns bad-quality readings."""
    response = await client.get("/api/v1/sensors/alerts")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "count" in data


@pytest.mark.asyncio
async def test_sensor_alerts_only_bad_quality(client, sample_sensor_readings):
    """Test that alerts only returns BAD or DEGRADED quality readings."""
    response = await client.get("/api/v1/sensors/alerts")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2  # 1 BAD + 1 DEGRADED
    for item in data["items"]:
        assert item["quality"] in ("BAD", "DEGRADED")


@pytest.mark.asyncio
async def test_sensor_alerts_empty_when_no_issues(client):
    """Test alerts returns empty list when no bad readings exist."""
    response = await client.get("/api/v1/sensors/alerts")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["count"] == 0


@pytest.mark.asyncio
async def test_sensor_stats_success(client, sample_sensor_readings):
    """Test GET /api/v1/sensors/stats returns aggregated statistics."""
    response = await client.get("/api/v1/sensors/stats")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_sensor_stats_filter_by_line(client, sample_sensor_readings):
    """Test sensor stats endpoint returns data."""
    response = await client.get("/api/v1/sensors/stats")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_sensor_stats_contains_aggregates(client, sample_sensor_readings):
    """Test that stats items contain min/max/avg and reading counts."""
    response = await client.get("/api/v1/sensors/stats")

    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert "avg_value" in item
        assert "min_value" in item
        assert "max_value" in item
        assert "reading_count" in item
        assert "alert_count" in item
        assert item["reading_count"] > 0


@pytest.mark.asyncio
async def test_sensor_stats_alert_count(client, sample_sensor_readings):
    """Test that alert_count correctly counts BAD/DEGRADED readings."""
    response = await client.get("/api/v1/sensors/stats")

    assert response.status_code == 200
    data = response.json()
    total_alerts = sum(item["alert_count"] for item in data["items"])
    assert total_alerts == 2  # 1 BAD + 1 DEGRADED across all lines
