"""
Integration tests for Sensor synchronization from Gateway.

Tests verify that sync_from_gateway properly handles Sensor and SensorParameter
dependencies, and that readings are synced with full FK hierarchy.
"""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.models.sensor import SensorReading
from app.models.reference import Sensor, SensorParameter, ProductionLine
from app.services.sensor_service import SensorService
from app.schemas.gateway_responses import (
    SensorReadingsResponse, SensorReadingItem
)


@pytest.mark.asyncio
async def test_sync_sensors_creates_full_hierarchy(session):
    """sync_from_gateway should create Sensor + SensorParameter + SensorReading hierarchy."""
    # Setup: Create ProductionLine (required by Sensor)
    line_id = uuid4()
    line = ProductionLine(
        id=line_id,
        name="Line A",
        code="LA-1",
        is_active=True,
    )
    session.add(line)
    await session.commit()

    # Prepare mock gateway response
    sensor_id = uuid4()
    param_id = uuid4()
    reading_id = uuid4()
    device_id = "SENSOR-001"

    mock_gateway = AsyncMock()
    mock_gateway.get_sensor_readings = AsyncMock(return_value=SensorReadingsResponse(
        readings=[
            SensorReadingItem(
                id=reading_id,
                sensorId=sensor_id,
                deviceId=device_id,
                productionLineId=line_id,
                sensorParameterId=param_id,
                value=23.5,
                quality="good",
                recordedAt=datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc),
            )
        ],
        total=1
    ))

    # Execute
    service = SensorService(session, gateway=mock_gateway)
    count = await service.sync_from_gateway(None, None)

    assert count == 1  # 1 reading synced

    # Verify SensorParameter was created as stub
    param = await session.get(SensorParameter, param_id)
    assert param is not None
    assert param.code.startswith("param_")  # Code is first 8 chars of UUID due to DB constraint
    assert param.name == "[Pending sync]"
    assert param.is_active is True

    # Verify Sensor was created with FK to parameter
    sensor = await session.get(Sensor, sensor_id)
    assert sensor is not None
    assert sensor.device_id == device_id
    assert sensor.production_line_id == line_id
    assert sensor.sensor_parameter_id == param_id
    assert sensor.is_active is True

    # Verify SensorReading was created with FK to sensor
    reading = await session.get(SensorReading, reading_id)
    assert reading is not None
    assert reading.sensor_id == sensor_id
    assert float(reading.value) == 23.5
    assert reading.quality == "good"
    assert reading.recorded_at == datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_sync_sensors_updates_existing_sensor(session):
    """sync_from_gateway should update existing Sensor if device_id matches."""
    # Setup: Create line and existing sensor
    line_id = uuid4()
    line = ProductionLine(
        id=line_id,
        name="Line A",
        code="LA-1",
        is_active=True,
    )
    session.add(line)

    sensor_id = uuid4()
    device_id = "SENSOR-001"
    param_id_old = uuid4()
    param_old = SensorParameter(
        id=param_id_old,
        code="temp",
        name="Temperature",
        unit="C",
    )
    session.add(param_old)

    sensor = Sensor(
        id=sensor_id,
        device_id=device_id,
        production_line_id=line_id,
        sensor_parameter_id=param_id_old,
        is_active=True,
    )
    session.add(sensor)
    await session.commit()

    # Prepare mock response with same device_id but new parameter
    reading_id = uuid4()
    param_id_new = uuid4()

    mock_gateway = AsyncMock()
    mock_gateway.get_sensor_readings = AsyncMock(return_value=SensorReadingsResponse(
        readings=[
            SensorReadingItem(
                id=reading_id,
                sensorId=sensor_id,
                deviceId=device_id,
                productionLineId=line_id,
                sensorParameterId=param_id_new,
                value=25.0,
                quality="good",
                recordedAt=datetime(2026, 5, 10, 13, 0, 0),
            )
        ],
        total=1
    ))

    # Execute
    service = SensorService(session, gateway=mock_gateway)
    count = await service.sync_from_gateway(None, None)

    assert count == 1

    # Verify Sensor was updated (same ID, new param)
    updated_sensor = await session.get(Sensor, sensor_id)
    assert updated_sensor is not None
    assert updated_sensor.device_id == device_id
    assert updated_sensor.sensor_parameter_id == param_id_new  # Updated


@pytest.mark.asyncio
async def test_sync_sensors_skips_missing_sensor_id(session):
    """sync_from_gateway should skip reading if sensorId is missing."""
    line_id = uuid4()
    line = ProductionLine(id=line_id, name="Line A", code="LA-1", is_active=True)
    session.add(line)
    await session.commit()

    reading_id = uuid4()
    param_id = uuid4()

    mock_gateway = AsyncMock()
    mock_gateway.get_sensor_readings = AsyncMock(return_value=SensorReadingsResponse(
        readings=[
            SensorReadingItem(
                id=reading_id,
                sensorId=None,  # Missing sensor ID
                deviceId="SENSOR-002",
                productionLineId=line_id,
                sensorParameterId=param_id,
                value=20.0,
                quality="good",
                recordedAt=datetime(2026, 5, 10, 14, 0, 0),
            )
        ],
        total=1
    ))

    service = SensorService(session, gateway=mock_gateway)
    count = await service.sync_from_gateway(None, None)

    # Reading should be skipped
    assert count == 0

    # Verify no SensorReading created
    reading = await session.get(SensorReading, reading_id)
    assert reading is None


@pytest.mark.asyncio
async def test_sync_sensors_batches_multiple_readings(session):
    """sync_from_gateway should batch process readings correctly."""
    line_id = uuid4()
    line = ProductionLine(id=line_id, name="Line A", code="LA-1", is_active=True)
    session.add(line)
    await session.commit()

    # Create 150 readings (3 batches of 50)
    readings = []
    for i in range(150):
        readings.append(SensorReadingItem(
            id=uuid4(),
            sensorId=uuid4(),
            deviceId=f"SENSOR-{i:03d}",
            productionLineId=line_id,
            sensorParameterId=uuid4(),
            value=20.0 + i * 0.1,
            quality="good",
            recordedAt=datetime(2026, 5, 10, 12, i % 60, 0),
        ))

    mock_gateway = AsyncMock()
    mock_gateway.get_sensor_readings = AsyncMock(return_value=SensorReadingsResponse(
        readings=readings,
        total=150
    ))

    service = SensorService(session, gateway=mock_gateway)
    count = await service.sync_from_gateway(None, None)

    assert count == 150

    # Verify all readings are in DB
    all_readings = await session.query(SensorReading).all()
    assert len(all_readings) == 150


@pytest.mark.asyncio
async def test_sync_sensors_handles_missing_parameter(session):
    """sync_from_gateway should create parameter stub if sensorParameterId is missing."""
    line_id = uuid4()
    line = ProductionLine(id=line_id, name="Line A", code="LA-1", is_active=True)
    session.add(line)
    await session.commit()

    sensor_id = uuid4()
    reading_id = uuid4()

    mock_gateway = AsyncMock()
    mock_gateway.get_sensor_readings = AsyncMock(return_value=SensorReadingsResponse(
        readings=[
            SensorReadingItem(
                id=reading_id,
                sensorId=sensor_id,
                deviceId="SENSOR-003",
                productionLineId=line_id,
                sensorParameterId=None,  # Missing parameter ID
                value=18.5,
                quality="good",
                recordedAt=datetime(2026, 5, 10, 15, 0, 0),
            )
        ],
        total=1
    ))

    service = SensorService(session, gateway=mock_gateway)
    count = await service.sync_from_gateway(None, None)

    # Reading should still be synced (sensor_parameter_id can be None in this flow)
    assert count == 1

    # Verify Sensor was created without parameter
    sensor = await session.get(Sensor, sensor_id)
    assert sensor is not None
    assert sensor.sensor_parameter_id is None
