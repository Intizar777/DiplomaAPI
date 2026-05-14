"""
Integration tests for Phase 4 cursor pagination on event-like feeds.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

import pytest
from app.models.analytics import BatchInput, DowntimeEvent


@pytest.mark.asyncio
async def test_batch_inputs_cursor_pagination(client, session):
    now = datetime.now(timezone.utc)
    rows = [
        BatchInput(
            order_id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            quantity=Decimal("10.000"),
            input_date=now - timedelta(minutes=idx),
        )
        for idx in range(4)
    ]
    session.add_all(rows)
    await session.commit()

    first = await client.get("/api/production/batch-inputs", params={"limit": 2, "cursor": ""})
    assert first.status_code == 200
    first_data = first.json()
    assert first_data["has_more"] is True
    assert first_data["next_cursor"] is not None
    assert len(first_data["items"]) == 2

    second = await client.get(
        "/api/production/batch-inputs",
        params={"limit": 2, "cursor": first_data["next_cursor"]},
    )
    assert second.status_code == 200
    second_data = second.json()
    assert len(second_data["items"]) >= 1

    first_ids = {item["id"] for item in first_data["items"]}
    second_ids = {item["id"] for item in second_data["items"]}
    assert first_ids.isdisjoint(second_ids)


@pytest.mark.asyncio
async def test_batch_inputs_invalid_cursor_returns_400(client):
    response = await client.get("/api/production/batch-inputs", params={"cursor": "invalid"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_downtime_events_cursor_pagination(client, session):
    now = datetime.now(timezone.utc)
    rows = [
        DowntimeEvent(
            production_line_id=uuid.uuid4(),
            reason=f"reason-{idx}",
            category="OTHER",
            started_at=now - timedelta(minutes=idx),
            ended_at=now - timedelta(minutes=idx - 1),
            duration_minutes=1,
        )
        for idx in range(4)
    ]
    session.add_all(rows)
    await session.commit()

    first = await client.get("/api/production/downtime-events", params={"limit": 2, "cursor": ""})
    assert first.status_code == 200
    first_data = first.json()
    assert first_data["has_more"] is True
    assert first_data["next_cursor"] is not None

    second = await client.get(
        "/api/production/downtime-events",
        params={"limit": 2, "cursor": first_data["next_cursor"]},
    )
    assert second.status_code == 200
    second_data = second.json()
    assert len(second_data["items"]) >= 1

    first_ids = {item["id"] for item in first_data["items"]}
    second_ids = {item["id"] for item in second_data["items"]}
    assert first_ids.isdisjoint(second_ids)


@pytest.mark.asyncio
async def test_downtime_events_invalid_cursor_returns_400(client):
    response = await client.get("/api/production/downtime-events", params={"cursor": "invalid"})
    assert response.status_code == 400
