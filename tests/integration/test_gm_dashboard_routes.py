"""
Integration tests for Group Manager Dashboard HTTP endpoints.

Uses httpx AsyncClient + testcontainers PostgreSQL (real DB, full request-response cycle).
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

from app.models.kpi import AggregatedKPI
from app.models.orders import OrderSnapshot


# ---------------------------------------------------------------------------
# Local fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sample_gm_kpi_data(session):
    """Insert 2 AggregatedKPI rows (Line-A, Line-B) within the last 15 days."""
    today = date.today()
    period_from = today - timedelta(days=15)

    records = [
        AggregatedKPI(
            period_from=period_from,
            period_to=today,
            production_line="Line-A",
            total_output=Decimal("1000"),
            defect_rate=Decimal("2.50"),
            completed_orders=8,
            total_orders=10,
            oee_estimate=Decimal("82.00"),
        ),
        AggregatedKPI(
            period_from=period_from,
            period_to=today,
            production_line="Line-B",
            total_output=Decimal("900"),
            defect_rate=Decimal("4.00"),
            completed_orders=6,
            total_orders=10,
            oee_estimate=Decimal("68.00"),
        ),
    ]
    for r in records:
        session.add(r)
    await session.commit()
    return records


@pytest_asyncio.fixture
async def sample_gm_order_data(session):
    """
    Insert 4 OrderSnapshot rows with snapshot_date = today - 5 days.
    Some with timestamps for downtime calculations, mixed statuses.
    """
    today = date.today()
    snap = today - timedelta(days=5)
    base_dt = datetime(today.year, today.month, today.day, 12, 0, 0, tzinfo=timezone.utc)

    records = [
        # Line-A: completed, on-time
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product X",
            target_quantity=Decimal("500"),
            actual_quantity=Decimal("490"),
            unit_of_measure="kg",
            status="completed",
            production_line="Line-A",
            planned_start=base_dt - timedelta(hours=8),
            planned_end=base_dt,
            actual_start=base_dt - timedelta(hours=8),
            actual_end=base_dt - timedelta(minutes=10),
            snapshot_date=snap,
        ),
        # Line-A: completed, delayed by 3h
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product X",
            target_quantity=Decimal("300"),
            actual_quantity=Decimal("280"),
            unit_of_measure="kg",
            status="completed",
            production_line="Line-A",
            planned_start=base_dt - timedelta(hours=6),
            planned_end=base_dt + timedelta(hours=2),
            actual_start=base_dt - timedelta(hours=6),
            actual_end=base_dt + timedelta(hours=5),  # +3h delay
            snapshot_date=snap,
        ),
        # Line-B: planned
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product Y",
            target_quantity=Decimal("400"),
            actual_quantity=Decimal("0"),
            unit_of_measure="kg",
            status="planned",
            production_line="Line-B",
            planned_start=base_dt + timedelta(hours=8),
            planned_end=base_dt + timedelta(hours=16),
            actual_start=None,
            actual_end=None,
            snapshot_date=snap,
        ),
        # Line-B: completed, delayed by 1h
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product Y",
            target_quantity=Decimal("600"),
            actual_quantity=Decimal("580"),
            unit_of_measure="kg",
            status="completed",
            production_line="Line-B",
            planned_start=base_dt - timedelta(hours=4),
            planned_end=base_dt + timedelta(hours=4),
            actual_start=base_dt - timedelta(hours=4),
            actual_end=base_dt + timedelta(hours=5),  # +1h delay
            snapshot_date=snap,
        ),
    ]
    for r in records:
        session.add(r)
    await session.commit()
    return records


# ---------------------------------------------------------------------------
# OEE summary endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_oee_summary_returns_200(client, sample_gm_kpi_data):
    """GET /gm/oee-summary?period_days=30 returns 200 with expected structure."""
    response = await client.get("/api/v1/dashboards/gm/oee-summary?period_days=30")
    assert response.status_code == 200
    data = response.json()
    assert "lines" in data
    assert "period_days" in data
    assert "oee_target" in data
    assert data["oee_target"] == "75.0"


@pytest.mark.asyncio
async def test_oee_summary_default_period_days(client, sample_gm_kpi_data):
    """GET /gm/oee-summary without params should default to period_days=30."""
    response = await client.get("/api/v1/dashboards/gm/oee-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["period_days"] == 30
    assert len(data["lines"]) > 0


@pytest.mark.asyncio
async def test_oee_summary_empty_database(client):
    """GET /gm/oee-summary with no data returns 200 with empty lines list."""
    response = await client.get("/api/v1/dashboards/gm/oee-summary?period_days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["lines"] == []


# ---------------------------------------------------------------------------
# Plan execution endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_plan_execution_returns_200(client, sample_gm_order_data):
    """GET /gm/plan-execution with explicit date range returns 200."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }
    response = await client.get("/api/v1/dashboards/gm/plan-execution", params=params)
    assert response.status_code == 200
    data = response.json()
    assert "lines" in data
    assert "total_target" in data
    assert "overall_fulfillment_pct" in data


@pytest.mark.asyncio
async def test_plan_execution_default_dates(client, sample_gm_order_data):
    """GET /gm/plan-execution without params uses default 30-day window and returns data."""
    response = await client.get("/api/v1/dashboards/gm/plan-execution")
    assert response.status_code == 200
    data = response.json()
    assert "period_from" in data
    assert "period_to" in data
    assert len(data["lines"]) > 0


# ---------------------------------------------------------------------------
# Downtime ranking endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_downtime_ranking_returns_200(client, sample_gm_order_data):
    """GET /gm/downtime-ranking with explicit date range returns 200."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }
    response = await client.get("/api/v1/dashboards/gm/downtime-ranking", params=params)
    assert response.status_code == 200
    data = response.json()
    assert "lines" in data
    assert "total_delay_hours" in data
    assert "total_delayed_orders" in data


@pytest.mark.asyncio
async def test_downtime_ranking_ranked_worst_first(client, sample_gm_order_data):
    """Lines in /gm/downtime-ranking response must be sorted descending by total_delay_hours."""
    response = await client.get("/api/v1/dashboards/gm/downtime-ranking")
    assert response.status_code == 200
    data = response.json()
    if len(data["lines"]) > 1:
        delays = [float(line["total_delay_hours"]) for line in data["lines"]]
        assert delays == sorted(delays, reverse=True)


@pytest.mark.asyncio
async def test_downtime_ranking_empty_database(client):
    """GET /gm/downtime-ranking with no data returns 200 with empty lines and zero totals."""
    response = await client.get("/api/v1/dashboards/gm/downtime-ranking")
    assert response.status_code == 200
    data = response.json()
    assert data["lines"] == []
    assert float(data["total_delay_hours"]) == 0
    assert data["total_delayed_orders"] == 0
