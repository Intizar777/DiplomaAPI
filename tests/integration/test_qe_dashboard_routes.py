"""
Integration tests for Quality Engineer Dashboard HTTP endpoints.

Uses httpx AsyncClient + testcontainers PostgreSQL (real DB, full request-response cycle).
"""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

from app.models.quality import QualityResult
from app.models.reference import QualitySpec
from app.models.output import ProductionOutput


# ---------------------------------------------------------------------------
# Local fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sample_qe_route_data(session):
    """
    Insert compact dataset for route integration tests.

    2 QualitySpec rows for pid_a.
    6 QualityResult rows:
      - 2 in-spec for Lot-A (pid_a)
      - 2 out-of-spec for Lot-B (pid_a)
      - 2 for pid_b (separate product)
    2 ProductionOutput rows for Lot-A and Lot-B.
    """
    today = date.today()
    period_from = today - timedelta(days=15)
    pid_a = uuid4()
    pid_b = uuid4()

    spec_ph = QualitySpec(
        product_id=pid_a, parameter_name="pH",
        lower_limit=Decimal("6.5"), upper_limit=Decimal("7.5"), is_active=True,
    )
    spec_viscosity = QualitySpec(
        product_id=pid_a, parameter_name="viscosity",
        lower_limit=Decimal("100"), upper_limit=Decimal("200"), is_active=True,
    )
    session.add(spec_ph)
    session.add(spec_viscosity)
    await session.flush()

    quality_rows = [
        # Lot-A in-spec
        QualityResult(
            lot_number="Lot-A", product_id=pid_a, parameter_name="pH",
            result_value=Decimal("7.0"), quality_spec_id=spec_ph.id, in_spec=True,
            decision="pass", test_date=period_from + timedelta(days=2),
        ),
        QualityResult(
            lot_number="Lot-A", product_id=pid_a, parameter_name="viscosity",
            result_value=Decimal("150"), quality_spec_id=spec_viscosity.id, in_spec=True,
            decision="pass", test_date=period_from + timedelta(days=2),
        ),
        # Lot-B out-of-spec
        QualityResult(
            lot_number="Lot-B", product_id=pid_a, parameter_name="pH",
            result_value=Decimal("8.8"), quality_spec_id=spec_ph.id, in_spec=False,
            decision="fail", test_date=period_from + timedelta(days=5),
        ),
        QualityResult(
            lot_number="Lot-B", product_id=pid_a, parameter_name="viscosity",
            result_value=Decimal("250"), quality_spec_id=spec_viscosity.id, in_spec=False,
            decision="fail", test_date=period_from + timedelta(days=5),
        ),
        # pid_b rows (separate product)
        QualityResult(
            lot_number="Lot-C", product_id=pid_b, parameter_name="pH",
            result_value=Decimal("6.0"), quality_spec_id=None, in_spec=False,
            decision="fail", test_date=period_from + timedelta(days=3),
        ),
        QualityResult(
            lot_number="Lot-C", product_id=pid_b, parameter_name="viscosity",
            result_value=Decimal("90"), quality_spec_id=None, in_spec=False,
            decision="fail", test_date=period_from + timedelta(days=3),
        ),
    ]
    for r in quality_rows:
        session.add(r)

    output_rows = [
        ProductionOutput(
            product_id=pid_a, product_name="Alpha", lot_number="Lot-A",
            production_date=period_from + timedelta(days=2), shift="Shift 1",
            snapshot_date=today,
        ),
        ProductionOutput(
            product_id=pid_a, product_name="Alpha", lot_number="Lot-B",
            production_date=period_from + timedelta(days=5), shift="Shift 2",
            snapshot_date=today,
        ),
    ]
    for r in output_rows:
        session.add(r)

    await session.commit()
    return {"pid_a": pid_a, "pid_b": pid_b}


# ---------------------------------------------------------------------------
# Parameter trends endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_parameter_trends_returns_200(client, sample_qe_route_data):
    """GET /qe/parameter-trends returns 200 with parameters key."""
    response = await client.get("/api/v1/dashboards/qe/parameter-trends")
    assert response.status_code == 200
    data = response.json()
    assert "parameters" in data
    assert len(data["parameters"]) >= 1


@pytest.mark.asyncio
async def test_parameter_trends_decimal_as_string(client, sample_qe_route_data):
    """avg_value and out_of_spec_pct must be serialized as strings (Decimal → JSON string)."""
    response = await client.get("/api/v1/dashboards/qe/parameter-trends")
    assert response.status_code == 200
    data = response.json()
    for param in data["parameters"]:
        for point in param["trend"]:
            assert isinstance(point["avg_value"], str)
            assert isinstance(point["out_of_spec_pct"], str)


# ---------------------------------------------------------------------------
# Batch analysis endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_batch_analysis_only_deviated_lots(client, sample_qe_route_data):
    """GET /qe/batch-analysis returns 200; all lots have fail_count>=1 and deviations key."""
    response = await client.get("/api/v1/dashboards/qe/batch-analysis")
    assert response.status_code == 200
    data = response.json()
    assert "lots" in data
    for lot in data["lots"]:
        assert lot["fail_count"] >= 1
        assert "deviations" in lot


# ---------------------------------------------------------------------------
# Defect Pareto endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_defect_pareto_returns_200(client, sample_qe_route_data):
    """GET /qe/defect-pareto returns 200 with parameters, total_defects, product_id."""
    response = await client.get("/api/v1/dashboards/qe/defect-pareto")
    assert response.status_code == 200
    data = response.json()
    assert "parameters" in data
    assert "total_defects" in data
    assert "product_id" in data
    assert data["product_id"] is None


@pytest.mark.asyncio
async def test_defect_pareto_product_filter(client, sample_qe_route_data):
    """?product_id=pid_a returns product_id=str(pid_a) and no pid_b contamination."""
    pid_a = sample_qe_route_data["pid_a"]
    response = await client.get(f"/api/v1/dashboards/qe/defect-pareto?product_id={pid_a}")
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == str(pid_a)
    # Only pid_a defects: pH=1 (Lot-B), viscosity=1 (Lot-B) → total=2
    assert data["total_defects"] == 2


# ---------------------------------------------------------------------------
# Empty database tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_all_endpoints_empty_database(client):
    """All 3 endpoints return 200 with empty lists and zero totals on empty DB."""
    resp_trends = await client.get("/api/v1/dashboards/qe/parameter-trends")
    assert resp_trends.status_code == 200
    assert resp_trends.json()["parameters"] == []

    resp_batch = await client.get("/api/v1/dashboards/qe/batch-analysis")
    assert resp_batch.status_code == 200
    assert resp_batch.json()["lots"] == []
    assert resp_batch.json()["lot_count"] == 0

    resp_pareto = await client.get("/api/v1/dashboards/qe/defect-pareto")
    assert resp_pareto.status_code == 200
    assert resp_pareto.json()["parameters"] == []
    assert resp_pareto.json()["total_defects"] == 0
