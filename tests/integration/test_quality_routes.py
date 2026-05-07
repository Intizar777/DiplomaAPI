"""
Integration tests for Quality API endpoints.

Tests full request-response cycles with real database.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
import pytest_asyncio

from app.models.quality import QualityResult


@pytest_asyncio.fixture
async def sample_quality_results(session):
    """Insert quality test results for testing."""
    today = date.today()
    product_id = uuid.uuid4()

    results = [
        # Lot-001: all approved, in spec
        QualityResult(
            lot_number="LOT-001",
            product_id=product_id,
            product_name="Product Alpha",
            parameter_name="pH",
            result_value=Decimal("7.0"),
            lower_limit=Decimal("6.5"),
            upper_limit=Decimal("7.5"),
            in_spec=True,
            decision="approved",
            test_date=today - timedelta(days=2),
        ),
        QualityResult(
            lot_number="LOT-001",
            product_id=product_id,
            product_name="Product Alpha",
            parameter_name="viscosity",
            result_value=Decimal("150"),
            lower_limit=Decimal("100"),
            upper_limit=Decimal("200"),
            in_spec=True,
            decision="approved",
            test_date=today - timedelta(days=2),
        ),
        # Lot-002: rejected, out of spec
        QualityResult(
            lot_number="LOT-002",
            product_id=product_id,
            product_name="Product Alpha",
            parameter_name="pH",
            result_value=Decimal("8.5"),
            lower_limit=Decimal("6.5"),
            upper_limit=Decimal("7.5"),
            in_spec=False,
            decision="rejected",
            test_date=today - timedelta(days=1),
        ),
        QualityResult(
            lot_number="LOT-002",
            product_id=product_id,
            product_name="Product Alpha",
            parameter_name="viscosity",
            result_value=Decimal("180"),
            lower_limit=Decimal("100"),
            upper_limit=Decimal("200"),
            in_spec=True,
            decision="rejected",
            test_date=today - timedelta(days=1),
        ),
        # Lot-003: pending
        QualityResult(
            lot_number="LOT-003",
            product_id=product_id,
            product_name="Product Alpha",
            parameter_name="pH",
            result_value=Decimal("7.1"),
            lower_limit=Decimal("6.5"),
            upper_limit=Decimal("7.5"),
            in_spec=True,
            decision="pending",
            test_date=today,
        ),
    ]
    session.add_all(results)
    await session.commit()
    return {"results": results, "product_id": product_id}


@pytest.mark.asyncio
async def test_quality_summary_success(client, sample_quality_results):
    """Test GET /api/v1/quality/summary returns quality statistics."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/quality/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "average_quality" in data
    assert "approved_count" in data
    assert "rejected_count" in data
    assert "pending_count" in data
    assert "defect_rate" in data
    assert "by_parameter" in data
    assert "period_from" in data
    assert "period_to" in data


@pytest.mark.asyncio
async def test_quality_summary_counts(client, sample_quality_results):
    """Test that summary returns correct decision counts."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/quality/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    # 2 approved tests, 2 rejected tests, 1 pending test
    assert data["approved_count"] == 2
    assert data["rejected_count"] == 2
    assert data["pending_count"] == 1


@pytest.mark.asyncio
async def test_quality_summary_defect_rate(client, sample_quality_results):
    """Test that defect_rate is calculated correctly."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/quality/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    # 2 rejected / 5 total = 40%
    assert Decimal(str(data["defect_rate"])) == Decimal("40.0")


@pytest.mark.asyncio
async def test_quality_summary_by_parameter(client, sample_quality_results):
    """Test that summary includes per-parameter breakdown."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/quality/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    by_param = data["by_parameter"]
    assert "pH" in by_param
    assert "viscosity" in by_param
    assert by_param["pH"]["tests_count"] == 3
    assert by_param["viscosity"]["tests_count"] == 2


@pytest.mark.asyncio
async def test_quality_summary_empty_for_future_dates(client):
    """Test that future date range returns zero counts."""
    future = date.today() + timedelta(days=100)
    params = {
        "date_from": str(future),
        "date_to": str(future + timedelta(days=30)),
    }

    response = await client.get("/api/v1/quality/summary", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["approved_count"] == 0
    assert data["rejected_count"] == 0
    assert data["defect_rate"] == "0"


@pytest.mark.asyncio
async def test_defect_trends_success(client, sample_quality_results):
    """Test GET /api/v1/quality/defect-trends returns trend data."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/quality/defect-trends", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert "period_from" in data
    assert "period_to" in data
    assert len(data["trends"]) > 0


@pytest.mark.asyncio
async def test_defect_trends_ordered_by_date(client, sample_quality_results):
    """Test that trend points are in chronological order."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/quality/defect-trends", params=params)

    assert response.status_code == 200
    data = response.json()
    dates = [item["trend_date"] for item in data["trends"]]
    assert dates == sorted(dates)


@pytest.mark.asyncio
async def test_defect_trends_contain_correct_fields(client, sample_quality_results):
    """Test that each trend point has required fields."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/quality/defect-trends", params=params)

    assert response.status_code == 200
    data = response.json()
    for point in data["trends"]:
        assert "trend_date" in point
        assert "defect_rate" in point
        assert "rejected_count" in point
        assert "total_tests" in point


@pytest.mark.asyncio
async def test_quality_lots_success(client, sample_quality_results):
    """Test GET /api/v1/quality/lots returns lot list."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
    }

    response = await client.get("/api/v1/quality/lots", params=params)

    assert response.status_code == 200
    data = response.json()
    assert "lots" in data
    assert "total" in data
    assert "approved_count" in data
    assert "rejected_count" in data
    assert "pending_count" in data
    assert data["total"] == 3  # LOT-001, LOT-002, LOT-003


@pytest.mark.asyncio
async def test_quality_lots_filter_by_decision(client, sample_quality_results):
    """Test filtering lots by decision."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "decision": "approved",
    }

    response = await client.get("/api/v1/quality/lots", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["lots"][0]["lot_number"] == "LOT-001"
    for lot in data["lots"]:
        assert lot["decision"] == "approved"


@pytest.mark.asyncio
async def test_quality_lots_parameters_counted(client, sample_quality_results):
    """Test that parameters_tested and parameters_passed are counted."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "decision": "approved",
    }

    response = await client.get("/api/v1/quality/lots", params=params)

    assert response.status_code == 200
    data = response.json()
    lot = data["lots"][0]
    assert lot["parameters_tested"] == 2  # pH + viscosity
    assert lot["parameters_passed"] == 2  # both in spec


@pytest.mark.asyncio
async def test_quality_lots_rejected_lot_parameters(client, sample_quality_results):
    """Test that rejected lot shows correct pass/fail parameter counts."""
    today = date.today()
    params = {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "decision": "rejected",
    }

    response = await client.get("/api/v1/quality/lots", params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    lot = data["lots"][0]
    assert lot["lot_number"] == "LOT-002"
    assert lot["parameters_tested"] == 2
    assert lot["parameters_passed"] == 1  # only viscosity passed
