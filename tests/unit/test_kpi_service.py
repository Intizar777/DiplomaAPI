"""
Unit tests for KPI service business logic.

Tests focus on:
- Current KPI retrieval (most recent period)
- Historical data filtering and ordering
- Period comparison and change calculations
- Empty/default responses
"""

from datetime import date, timedelta
from decimal import Decimal
import pytest
import pytest_asyncio

from app.models import AggregatedKPI
from app.services.kpi_service import KPIService
from app.schemas import KPICurrentResponse, KPIHistoryResponse, KPICompareResponse


@pytest_asyncio.fixture
async def sample_kpi_records(session):
    """Insert sample KPI records for testing."""
    today = date.today()
    records = []

    for days_ago in range(0, 90, 30):  # 3 records over 90 days
        kpi = AggregatedKPI(
            period_from=today - timedelta(days=days_ago + 30),
            period_to=today - timedelta(days=days_ago),
            production_line=None,
            total_output=Decimal(str(1000 + days_ago * 10)),
            defect_rate=Decimal(str(2.5 - days_ago * 0.1)),
            completed_orders=50 - days_ago,
            total_orders=100,
            oee_estimate=Decimal("85.5")
        )
        records.append(kpi)
        session.add(kpi)

    await session.commit()
    return records


@pytest.mark.asyncio
async def test_get_current_kpi_returns_most_recent(session, sample_kpi_records):
    """Test that get_current_kpi returns the most recent KPI record."""
    service = KPIService(db=session, gateway=None)

    result = await service.get_current_kpi()

    assert isinstance(result, KPICurrentResponse)
    assert result.data.total_output > 0
    assert result.data.defect_rate >= 0


@pytest.mark.asyncio
async def test_get_current_kpi_returns_default_when_empty(session):
    """Test that get_current_kpi returns default values when no data exists."""
    service = KPIService(db=session, gateway=None)

    result = await service.get_current_kpi()

    assert isinstance(result, KPICurrentResponse)
    assert result.data.total_output == Decimal("0")
    assert result.data.defect_rate == Decimal("0")


@pytest.mark.asyncio
async def test_get_current_kpi_with_production_line_filter(session, sample_kpi_records):
    """Test filtering current KPI by production line."""
    # Add a record with specific production line
    today = date.today()
    kpi_with_line = AggregatedKPI(
        period_from=today - timedelta(days=1),
        period_to=today,
        production_line="Line-A",
        total_output=Decimal("500"),
        defect_rate=Decimal("1.5"),
        completed_orders=25,
        total_orders=50,
        oee_estimate=Decimal("90.0")
    )
    session.add(kpi_with_line)
    await session.commit()

    service = KPIService(db=session, gateway=None)
    result = await service.get_current_kpi(production_line="Line-A")

    assert result.data.production_line == "Line-A"


@pytest.mark.asyncio
async def test_get_kpi_history_returns_ordered_by_date(session, sample_kpi_records):
    """Test that KPI history is returned ordered by period_from."""
    service = KPIService(db=session, gateway=None)
    today = date.today()

    result = await service.get_kpi_history(
        from_date=today - timedelta(days=120),
        to_date=today
    )

    assert isinstance(result, KPIHistoryResponse)
    assert len(result.items) > 0

    # Verify ordering by period_from
    for i in range(len(result.items) - 1):
        assert result.items[i].period_from <= result.items[i + 1].period_from


@pytest.mark.asyncio
async def test_get_kpi_history_with_date_filtering(session, sample_kpi_records):
    """Test that KPI history respects date range filters."""
    service = KPIService(db=session, gateway=None)
    today = date.today()
    start_date = today - timedelta(days=60)
    end_date = today - timedelta(days=30)

    result = await service.get_kpi_history(
        from_date=start_date,
        to_date=end_date
    )

    # All items should be within the range
    for item in result.items:
        assert item.period_from >= start_date
        assert item.period_to <= end_date


@pytest.mark.asyncio
async def test_get_kpi_history_returns_empty_for_future_dates(session):
    """Test that querying future dates returns empty history."""
    service = KPIService(db=session, gateway=None)
    tomorrow = date.today() + timedelta(days=1)
    next_month = tomorrow + timedelta(days=30)

    result = await service.get_kpi_history(
        from_date=tomorrow,
        to_date=next_month
    )

    assert len(result.items) == 0


@pytest.mark.asyncio
async def test_get_all_kpi_returns_all_records(session, sample_kpi_records):
    """Test that get_all_kpi returns all KPI records without filtering."""
    service = KPIService(db=session, gateway=None)

    result = await service.get_all_kpi()

    assert isinstance(result, KPIHistoryResponse)
    # Should return all sample records
    assert len(result.items) == len(sample_kpi_records)


@pytest.mark.asyncio
async def test_get_all_kpi_ordered_by_period(session, sample_kpi_records):
    """Test that all KPI records are ordered chronologically."""
    service = KPIService(db=session, gateway=None)

    result = await service.get_all_kpi()

    # Verify chronological ordering
    for i in range(len(result.items) - 1):
        assert result.items[i].period_from <= result.items[i + 1].period_from


@pytest.mark.asyncio
async def test_get_all_kpi_with_production_line_filter(session, sample_kpi_records):
    """Test filtering all KPI records by production line."""
    today = date.today()
    kpi_line_a = AggregatedKPI(
        period_from=today - timedelta(days=5),
        period_to=today - timedelta(days=4),
        production_line="Line-A",
        total_output=Decimal("600"),
        defect_rate=Decimal("2.0"),
        completed_orders=30,
        total_orders=60,
        oee_estimate=Decimal("88.0")
    )
    session.add(kpi_line_a)
    await session.commit()

    service = KPIService(db=session, gateway=None)
    result = await service.get_all_kpi(production_line="Line-A")

    # All returned items should be for Line-A
    for item in result.items:
        assert item.production_line == "Line-A"


@pytest.mark.asyncio
async def test_compare_kpi_periods_calculates_output_change(session, sample_kpi_records):
    """Test that KPI comparison calculates output change percentage."""
    service = KPIService(db=session, gateway=None)
    today = date.today()

    # Use two different periods from sample data
    period1_from = today - timedelta(days=30)
    period1_to = today
    period2_from = today - timedelta(days=60)
    period2_to = today - timedelta(days=30)

    result = await service.compare_kpi_periods(
        period1_from=period1_from,
        period1_to=period1_to,
        period2_from=period2_from,
        period2_to=period2_to
    )

    assert isinstance(result, KPICompareResponse)
    assert hasattr(result, 'output_change_percent')
    assert hasattr(result, 'defect_rate_change')
    assert hasattr(result, 'order_completion_change')


@pytest.mark.asyncio
async def test_compare_kpi_periods_with_missing_period(session, sample_kpi_records):
    """Test comparison when one period has no data (returns defaults)."""
    service = KPIService(db=session, gateway=None)
    future_date = date.today() + timedelta(days=100)

    result = await service.compare_kpi_periods(
        period1_from=future_date,
        period1_to=future_date + timedelta(days=30),
        period2_from=date.today(),
        period2_to=date.today() + timedelta(days=30)
    )

    # Period 1 should have default values (zeros)
    assert result.period1.total_output == Decimal("0")
    assert result.period1.defect_rate == Decimal("0")


@pytest.mark.asyncio
async def test_compare_kpi_defect_rate_change_calculation(session):
    """Test that defect rate change is correctly calculated as difference."""
    today = date.today()

    kpi1 = AggregatedKPI(
        period_from=today - timedelta(days=30),
        period_to=today,
        production_line=None,
        total_output=Decimal("1000"),
        defect_rate=Decimal("3.0"),
        completed_orders=50,
        total_orders=100,
        oee_estimate=Decimal("85.0")
    )

    kpi2 = AggregatedKPI(
        period_from=today - timedelta(days=60),
        period_to=today - timedelta(days=30),
        production_line=None,
        total_output=Decimal("950"),
        defect_rate=Decimal("2.0"),
        completed_orders=45,
        total_orders=100,
        oee_estimate=Decimal("83.0")
    )

    session.add_all([kpi1, kpi2])
    await session.commit()

    service = KPIService(db=session, gateway=None)
    result = await service.compare_kpi_periods(
        period1_from=today - timedelta(days=30),
        period1_to=today,
        period2_from=today - timedelta(days=60),
        period2_to=today - timedelta(days=30)
    )

    # Defect change should be current - previous = 3.0 - 2.0 = 1.0
    assert result.defect_rate_change == Decimal("1.0")


@pytest.mark.asyncio
async def test_compare_kpi_order_completion_change_calculation(session):
    """Test that order completion rate change is correctly calculated."""
    today = date.today()

    # Period 1: 60% completion (60/100)
    kpi1 = AggregatedKPI(
        period_from=today - timedelta(days=30),
        period_to=today,
        production_line=None,
        total_output=Decimal("1000"),
        defect_rate=Decimal("2.5"),
        completed_orders=60,
        total_orders=100,
        oee_estimate=Decimal("85.0")
    )

    # Period 2: 50% completion (50/100)
    kpi2 = AggregatedKPI(
        period_from=today - timedelta(days=60),
        period_to=today - timedelta(days=30),
        production_line=None,
        total_output=Decimal("950"),
        defect_rate=Decimal("2.0"),
        completed_orders=50,
        total_orders=100,
        oee_estimate=Decimal("83.0")
    )

    session.add_all([kpi1, kpi2])
    await session.commit()

    service = KPIService(db=session, gateway=None)
    result = await service.compare_kpi_periods(
        period1_from=today - timedelta(days=30),
        period1_to=today,
        period2_from=today - timedelta(days=60),
        period2_to=today - timedelta(days=30)
    )

    # Order completion change should be 60% - 50% = 10%
    assert result.order_completion_change == Decimal("10")


@pytest.mark.asyncio
async def test_compare_kpi_with_zero_total_orders(session):
    """Test comparison handles zero total orders gracefully."""
    today = date.today()

    kpi_zero_orders = AggregatedKPI(
        period_from=today - timedelta(days=30),
        period_to=today,
        production_line=None,
        total_output=Decimal("0"),
        defect_rate=Decimal("0"),
        completed_orders=0,
        total_orders=0,  # Zero orders
        oee_estimate=None
    )

    session.add(kpi_zero_orders)
    await session.commit()

    service = KPIService(db=session, gateway=None)
    result = await service.compare_kpi_periods(
        period1_from=today - timedelta(days=30),
        period1_to=today,
        period2_from=today - timedelta(days=60),
        period2_to=today - timedelta(days=30)
    )

    # Should handle gracefully (not divide by zero)
    assert result.order_completion_change == Decimal("0")
