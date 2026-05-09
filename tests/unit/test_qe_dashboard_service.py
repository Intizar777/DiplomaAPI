"""
Unit tests for QualityEngineerDashboardService.

Uses testcontainers PostgreSQL (real DB, not mocks).
"""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

from app.models.quality import QualityResult
from app.models.reference import QualitySpec
from app.models.output import ProductionOutput
from app.services.qe_dashboard_service import QualityEngineerDashboardService
from app.schemas.qe_dashboard import (
    ParameterTrendsResponse,
    BatchAnalysisResponse,
    DefectParetoResponse,
)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sample_qe_data(session):
    """
    Insert test data for QE dashboard tests.

    2 QualitySpec: spec_ph (pH, 6.5–7.5), spec_viscosity (viscosity, 100–200), both for pid_a.

    8 QualityResult rows:
      - today-5: Lot-001 pH=7.0 ✓, Lot-001 viscosity=150 ✓, Lot-002 pH=8.5 ✗ (>7.5)
      - today-3: Lot-003 pH=6.0 ✗ (<6.5), Lot-003 viscosity=250 ✗ (>200), Lot-004 pH=7.2 ✓, Lot-004 viscosity=180 ✓
      - today-60: Lot-OLD pH=5.0 ✗ (outside 30-day window)

    4 ProductionOutput: Lot-001/002 = Alpha / Shift 2, Lot-003/004 = Beta / Shift 1.
    """
    today = date.today()
    day_minus_5 = today - timedelta(days=5)
    day_minus_3 = today - timedelta(days=3)
    day_minus_60 = today - timedelta(days=60)

    pid_a = uuid4()

    spec_ph = QualitySpec(
        product_id=pid_a,
        parameter_name="pH",
        lower_limit=Decimal("6.5"),
        upper_limit=Decimal("7.5"),
        is_active=True,
    )
    spec_viscosity = QualitySpec(
        product_id=pid_a,
        parameter_name="viscosity",
        lower_limit=Decimal("100"),
        upper_limit=Decimal("200"),
        is_active=True,
    )
    session.add(spec_ph)
    session.add(spec_viscosity)
    await session.flush()

    quality_rows = [
        # today-5
        QualityResult(
            lot_number="Lot-001", product_id=pid_a, parameter_name="pH",
            result_value=Decimal("7.0"), quality_spec_id=spec_ph.id, in_spec=True,
            decision="pass", test_date=day_minus_5,
        ),
        QualityResult(
            lot_number="Lot-001", product_id=pid_a, parameter_name="viscosity",
            result_value=Decimal("150"), quality_spec_id=spec_viscosity.id, in_spec=True,
            decision="pass", test_date=day_minus_5,
        ),
        QualityResult(
            lot_number="Lot-002", product_id=pid_a, parameter_name="pH",
            result_value=Decimal("8.5"), quality_spec_id=spec_ph.id, in_spec=False,
            decision="fail", test_date=day_minus_5,
        ),
        # today-3
        QualityResult(
            lot_number="Lot-003", product_id=pid_a, parameter_name="pH",
            result_value=Decimal("6.0"), quality_spec_id=spec_ph.id, in_spec=False,
            decision="fail", test_date=day_minus_3,
        ),
        QualityResult(
            lot_number="Lot-003", product_id=pid_a, parameter_name="viscosity",
            result_value=Decimal("250"), quality_spec_id=spec_viscosity.id, in_spec=False,
            decision="fail", test_date=day_minus_3,
        ),
        QualityResult(
            lot_number="Lot-004", product_id=pid_a, parameter_name="pH",
            result_value=Decimal("7.2"), quality_spec_id=spec_ph.id, in_spec=True,
            decision="pass", test_date=day_minus_3,
        ),
        QualityResult(
            lot_number="Lot-004", product_id=pid_a, parameter_name="viscosity",
            result_value=Decimal("180"), quality_spec_id=spec_viscosity.id, in_spec=True,
            decision="pass", test_date=day_minus_3,
        ),
        # today-60 (outside 30-day window)
        QualityResult(
            lot_number="Lot-OLD", product_id=pid_a, parameter_name="pH",
            result_value=Decimal("5.0"), quality_spec_id=spec_ph.id, in_spec=False,
            decision="fail", test_date=day_minus_60,
        ),
    ]
    for r in quality_rows:
        session.add(r)

    output_rows = [
        ProductionOutput(
            product_id=pid_a, product_name="Alpha", lot_number="Lot-001",
            production_date=day_minus_5, shift="Shift 2", snapshot_date=today,
        ),
        ProductionOutput(
            product_id=pid_a, product_name="Alpha", lot_number="Lot-002",
            production_date=day_minus_5, shift="Shift 2", snapshot_date=today,
        ),
        ProductionOutput(
            product_id=pid_a, product_name="Beta", lot_number="Lot-003",
            production_date=day_minus_3, shift="Shift 1", snapshot_date=today,
        ),
        ProductionOutput(
            product_id=pid_a, product_name="Beta", lot_number="Lot-004",
            production_date=day_minus_3, shift="Shift 1", snapshot_date=today,
        ),
    ]
    for r in output_rows:
        session.add(r)

    await session.commit()
    return {"pid_a": pid_a, "spec_ph": spec_ph, "spec_viscosity": spec_viscosity}


# ---------------------------------------------------------------------------
# Parameter trends tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_parameter_trends_returns_both_parameters(session, sample_qe_data):
    """Two distinct parameters (pH + viscosity) must be returned."""
    today = date.today()
    service = QualityEngineerDashboardService(db=session)
    result = await service.get_parameter_trends(today - timedelta(days=30), today)

    assert isinstance(result, ParameterTrendsResponse)
    param_names = {p.parameter_name for p in result.parameters}
    assert param_names == {"pH", "viscosity"}


@pytest.mark.asyncio
async def test_parameter_trends_daily_out_of_spec_pct(session, sample_qe_data):
    """pH on today-5: test_count=2, out_of_spec=1, pct=50.00."""
    today = date.today()
    day_minus_5 = today - timedelta(days=5)
    service = QualityEngineerDashboardService(db=session)
    result = await service.get_parameter_trends(today - timedelta(days=30), today)

    ph = next(p for p in result.parameters if p.parameter_name == "pH")
    day5_point = next(pt for pt in ph.trend if pt.test_date == day_minus_5)

    assert day5_point.test_count == 2
    assert day5_point.out_of_spec_count == 1
    assert day5_point.out_of_spec_pct == Decimal("50.00")


@pytest.mark.asyncio
async def test_parameter_trends_spec_limits_attached(session, sample_qe_data):
    """pH trend points must carry lower_limit=6.5, upper_limit=7.5."""
    today = date.today()
    service = QualityEngineerDashboardService(db=session)
    result = await service.get_parameter_trends(today - timedelta(days=30), today)

    ph = next(p for p in result.parameters if p.parameter_name == "pH")
    for point in ph.trend:
        assert point.lower_limit == Decimal("6.5")
        assert point.upper_limit == Decimal("7.5")


@pytest.mark.asyncio
async def test_parameter_trends_excludes_old_records(session, sample_qe_data):
    """today-60 row must be excluded; pH total_tests=4, not 5."""
    today = date.today()
    service = QualityEngineerDashboardService(db=session)
    result = await service.get_parameter_trends(today - timedelta(days=30), today)

    ph = next(p for p in result.parameters if p.parameter_name == "pH")
    assert ph.total_tests == 4


# ---------------------------------------------------------------------------
# Batch analysis tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_batch_analysis_only_lots_with_deviations(session, sample_qe_data):
    """Only Lot-002 and Lot-003 have deviations; Lot-001 and Lot-004 must be absent."""
    today = date.today()
    service = QualityEngineerDashboardService(db=session)
    result = await service.get_batch_analysis(today - timedelta(days=30), today)

    assert isinstance(result, BatchAnalysisResponse)
    assert result.lot_count == 2
    lot_numbers = {lot.lot_number for lot in result.lots}
    assert lot_numbers == {"Lot-002", "Lot-003"}


@pytest.mark.asyncio
async def test_batch_analysis_deviation_magnitude_upper_breach(session, sample_qe_data):
    """Lot-002 pH=8.5 vs upper=7.5 → deviation_magnitude=1.0000."""
    today = date.today()
    service = QualityEngineerDashboardService(db=session)
    result = await service.get_batch_analysis(today - timedelta(days=30), today)

    lot_002 = next(lot for lot in result.lots if lot.lot_number == "Lot-002")
    ph_dev = next(d for d in lot_002.deviations if d.parameter_name == "pH")
    assert ph_dev.deviation_magnitude == Decimal("1.0000")


@pytest.mark.asyncio
async def test_batch_analysis_production_metadata_attached(session, sample_qe_data):
    """Lot-003 must have product_name='Beta' and shift='Shift 1'."""
    today = date.today()
    service = QualityEngineerDashboardService(db=session)
    result = await service.get_batch_analysis(today - timedelta(days=30), today)

    lot_003 = next(lot for lot in result.lots if lot.lot_number == "Lot-003")
    assert lot_003.product_name == "Beta"
    assert lot_003.shift == "Shift 1"


@pytest.mark.asyncio
async def test_batch_analysis_empty_when_all_in_spec(session):
    """All in-spec rows → lots==[], lot_count==0."""
    today = date.today()
    pid = uuid4()

    spec = QualitySpec(
        product_id=pid, parameter_name="pH",
        lower_limit=Decimal("6.0"), upper_limit=Decimal("8.0"), is_active=True,
    )
    session.add(spec)
    await session.flush()

    for i in range(3):
        r = QualityResult(
            lot_number=f"Good-Lot-{i}", product_id=pid, parameter_name="pH",
            result_value=Decimal("7.0"), quality_spec_id=spec.id, in_spec=True,
            decision="pass", test_date=today - timedelta(days=i + 1),
        )
        session.add(r)
    await session.commit()

    service = QualityEngineerDashboardService(db=session)
    result = await service.get_batch_analysis(today - timedelta(days=30), today)

    assert result.lots == []
    assert result.lot_count == 0


# ---------------------------------------------------------------------------
# Defect Pareto tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_defect_pareto_ranked_descending_and_cumulative(session, sample_qe_data):
    """pH (2 defects) must rank first, viscosity (1) second; cumulative non-decreasing; last=100.00."""
    today = date.today()
    service = QualityEngineerDashboardService(db=session)
    result = await service.get_defect_pareto(today - timedelta(days=30), today)

    assert isinstance(result, DefectParetoResponse)
    assert len(result.parameters) == 2

    # Ranked descending
    assert result.parameters[0].parameter_name == "pH"
    assert result.parameters[0].defect_count == 2
    assert result.parameters[1].parameter_name == "viscosity"
    assert result.parameters[1].defect_count == 1

    # Cumulative % non-decreasing
    cumulative = [p.cumulative_pct for p in result.parameters]
    assert cumulative == sorted(cumulative)
    # Last must be 100.00
    assert cumulative[-1] == Decimal("100.00")
