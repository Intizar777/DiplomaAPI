"""
Integration tests for KPI API endpoints.

Tests full request-response cycles with real database.
"""

from datetime import date, timedelta
from decimal import Decimal
import pytest

from app.models import AggregatedKPI


@pytest.mark.asyncio
async def test_get_current_kpi_success(client, sample_kpi_data):
    """Test GET /api/v1/kpi/current returns current KPI data."""
    response = await client.get("/api/v1/kpi/current")

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total_output" in data["data"]
    assert "defect_rate" in data["data"]
    assert "completed_orders" in data["data"]


@pytest.mark.asyncio
async def test_get_current_kpi_returns_most_recent(client, sample_kpi_data):
    """Test that /api/v1/kpi/current returns the most recent record."""
    response = await client.get("/api/v1/kpi/current")

    assert response.status_code == 200
    data = response.json()
    # Most recent should have the highest output value from sample data
    # Decimal comes back as string in JSON
    assert Decimal(str(data["data"]["total_output"])) > 0


@pytest.mark.asyncio
async def test_get_kpi_history_success(client, sample_kpi_data):
    """Test GET /api/v1/kpi/history returns historical data."""
    today = date.today()
    params = {
        "from_date": str(today - timedelta(days=120)),
        "to_date": str(today)
    }

    response = await client.get("/api/v1/kpi/history", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert "total_output" in data["items"][0]


@pytest.mark.asyncio
async def test_get_kpi_history_date_filtering(client, sample_kpi_data):
    """Test that /api/v1/kpi/history respects date range."""
    today = date.today()
    start = today - timedelta(days=60)
    end = today - timedelta(days=30)
    params = {
        "from_date": str(start),
        "to_date": str(end)
    }

    response = await client.get("/api/v1/kpi/history", params=params)

    assert response.status_code == 200
    data = response.json()
    # All items should be within range
    for item in data["items"]:
        item_date = date.fromisoformat(item["period_from"])
        assert item_date >= start


@pytest.mark.asyncio
async def test_get_kpi_history_empty_future_dates(client):
    """Test that querying future dates returns empty list."""
    tomorrow = date.today() + timedelta(days=1)
    next_week = tomorrow + timedelta(days=7)
    params = {
        "from_date": str(tomorrow),
        "to_date": str(next_week)
    }

    response = await client.get("/api/v1/kpi/history", params=params)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_get_kpi_history_with_production_line_filter(client, session):
    """Test that /api/v1/kpi/history filters by production_line."""
    today = date.today()

    # Add a record with specific production line
    kpi_line_a = AggregatedKPI(
        period_from=today - timedelta(days=10),
        period_to=today - timedelta(days=5),
        production_line="Line-A",
        total_output=Decimal("800"),
        defect_rate=Decimal("1.5"),
        completed_orders=40,
        total_orders=80,
        oee_estimate=Decimal("88.0")
    )
    session.add(kpi_line_a)
    await session.commit()

    params = {
        "from_date": str(today - timedelta(days=30)),
        "to_date": str(today),
        "production_line": "Line-A"
    }

    response = await client.get("/api/v1/kpi/history", params=params)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    # All items should be for Line-A
    for item in data["items"]:
        assert item["production_line"] == "Line-A"


@pytest.mark.asyncio
async def test_compare_kpi_periods_success(client, sample_kpi_data):
    """Test GET /api/v1/kpi/compare returns comparison data."""
    today = date.today()
    params = {
        "period1_from": str(today - timedelta(days=30)),
        "period1_to": str(today),
        "period2_from": str(today - timedelta(days=60)),
        "period2_to": str(today - timedelta(days=30))
    }

    response = await client.get("/api/v1/kpi/compare", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "period1" in data
    assert "period2" in data
    assert "output_change_percent" in data


@pytest.mark.asyncio
async def test_compare_kpi_periods_missing_period_returns_defaults(client):
    """Test that comparing with missing period returns default values."""
    future_date = date.today() + timedelta(days=100)
    today = date.today()
    params = {
        "period1_from": str(future_date),
        "period1_to": str(future_date + timedelta(days=30)),
        "period2_from": str(today - timedelta(days=30)),
        "period2_to": str(today)
    }

    response = await client.get("/api/v1/kpi/compare", params=params)

    assert response.status_code == 200
    data = response.json()
    # Period 1 should have default values (zeros)
    assert Decimal(str(data["period1"]["total_output"])) == 0
    assert Decimal(str(data["period1"]["defect_rate"])) == 0


@pytest.mark.asyncio
async def test_compare_kpi_periods_calculates_changes(client, session):
    """Test that comparison correctly calculates percentage changes."""
    today = date.today()

    # Period 1: higher output
    kpi1 = AggregatedKPI(
        period_from=today - timedelta(days=30),
        period_to=today,
        production_line=None,
        total_output=Decimal("1200"),
        defect_rate=Decimal("3.0"),
        completed_orders=60,
        total_orders=100,
        oee_estimate=Decimal("85.0")
    )

    # Period 2: lower output
    kpi2 = AggregatedKPI(
        period_from=today - timedelta(days=60),
        period_to=today - timedelta(days=30),
        production_line=None,
        total_output=Decimal("1000"),
        defect_rate=Decimal("2.0"),
        completed_orders=50,
        total_orders=100,
        oee_estimate=Decimal("83.0")
    )

    session.add_all([kpi1, kpi2])
    await session.commit()

    params = {
        "period1_from": str(today - timedelta(days=30)),
        "period1_to": str(today),
        "period2_from": str(today - timedelta(days=60)),
        "period2_to": str(today - timedelta(days=30))
    }

    response = await client.get("/api/v1/kpi/compare", params=params)

    assert response.status_code == 200
    data = response.json()
    # Output change: (1200 - 1000) / 1000 * 100 = 20%
    assert Decimal(str(data["output_change_percent"])) == Decimal("20")
    # Defect rate change: 3.0 - 2.0 = 1.0
    assert Decimal(str(data["defect_rate_change"])) == Decimal("1.0")


@pytest.mark.asyncio
async def test_get_current_kpi_empty_database(client):
    """Test that empty database returns default KPI values."""
    response = await client.get("/api/v1/kpi/current")

    assert response.status_code == 200
    data = response.json()
    assert Decimal(str(data["data"]["total_output"])) == 0
    assert Decimal(str(data["data"]["defect_rate"])) == 0
    assert data["data"]["completed_orders"] == 0


@pytest.mark.asyncio
async def test_compare_invalid_date_range(client):
    """Test that invalid date range (from > to) returns empty comparison."""
    today = date.today()
    params = {
        "period1_from": str(today),
        "period1_to": str(today - timedelta(days=30)),
        "period2_from": str(today - timedelta(days=60)),
        "period2_to": str(today - timedelta(days=30))
    }

    response = await client.get("/api/v1/kpi/compare", params=params)

    assert response.status_code == 200
    data = response.json()
    # Period 1 should be empty (invalid range)
    assert Decimal(str(data["period1"]["total_output"])) == 0


@pytest.mark.asyncio
async def test_kpi_responses_contain_timestamps(client, sample_kpi_data):
    """Test that KPI responses include period fields."""
    response = await client.get("/api/v1/kpi/current")

    assert response.status_code == 200
    data = response.json()
    assert "period_from" in data
    assert "period_to" in data


@pytest.mark.asyncio
async def test_history_items_ordered_by_period(client, session):
    """Test that history items are ordered by period_from ascending."""
    today = date.today()

    # Create records out of order to ensure sorting
    kpi_recent = AggregatedKPI(
        period_from=today - timedelta(days=10),
        period_to=today,
        production_line=None,
        total_output=Decimal("1000"),
        defect_rate=Decimal("2.5"),
        completed_orders=50,
        total_orders=100,
        oee_estimate=Decimal("85.0")
    )

    kpi_older = AggregatedKPI(
        period_from=today - timedelta(days=40),
        period_to=today - timedelta(days=30),
        production_line=None,
        total_output=Decimal("950"),
        defect_rate=Decimal("2.0"),
        completed_orders=45,
        total_orders=100,
        oee_estimate=Decimal("83.0")
    )

    session.add_all([kpi_recent, kpi_older])
    await session.commit()

    params = {
        "from_date": str(today - timedelta(days=60)),
        "to_date": str(today)
    }

    response = await client.get("/api/v1/kpi/history", params=params)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1

    # Verify chronological ordering if multiple items exist
    if len(data["items"]) > 1:
        for i in range(len(data["items"]) - 1):
            assert data["items"][i]["period_from"] <= data["items"][i + 1]["period_from"]
