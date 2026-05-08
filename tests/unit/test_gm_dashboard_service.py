"""
Unit tests for GroupManagerDashboardService.

Uses testcontainers PostgreSQL (real DB, not mocks).
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

from app.models.kpi import AggregatedKPI
from app.models.orders import OrderSnapshot
from app.services.gm_dashboard_service import GroupManagerDashboardService
from app.schemas.gm_dashboard import (
    OEESummaryResponse,
    PlanExecutionResponse,
    DowntimeRankingResponse,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sample_kpi_records(session):
    """
    Insert AggregatedKPI rows for 3 groups:
      - "Line-A": oee=85, 80  (avg 82.5)
      - "Line-B": oee=70, 65  (avg 67.5)
      - NULL line: oee=78, 76  (avg 77.0)
    Plus 1 old record (100 days ago) to verify period filtering.
    """
    today = date.today()
    recent = today - timedelta(days=10)
    old = today - timedelta(days=100)

    records = [
        # Line-A — two recent records
        AggregatedKPI(
            period_from=recent,
            period_to=today,
            production_line="Line-A",
            total_output=Decimal("1000"),
            defect_rate=Decimal("2.00"),
            completed_orders=8,
            total_orders=10,
            oee_estimate=Decimal("85.00"),
        ),
        AggregatedKPI(
            period_from=recent - timedelta(days=5),
            period_to=recent,
            production_line="Line-A",
            total_output=Decimal("900"),
            defect_rate=Decimal("3.00"),
            completed_orders=7,
            total_orders=10,
            oee_estimate=Decimal("80.00"),
        ),
        # Line-B — two recent records
        AggregatedKPI(
            period_from=recent,
            period_to=today,
            production_line="Line-B",
            total_output=Decimal("800"),
            defect_rate=Decimal("5.00"),
            completed_orders=6,
            total_orders=10,
            oee_estimate=Decimal("70.00"),
        ),
        AggregatedKPI(
            period_from=recent - timedelta(days=5),
            period_to=recent,
            production_line="Line-B",
            total_output=Decimal("750"),
            defect_rate=Decimal("6.00"),
            completed_orders=5,
            total_orders=10,
            oee_estimate=Decimal("65.00"),
        ),
        # NULL line — two recent records
        AggregatedKPI(
            period_from=recent,
            period_to=today,
            production_line=None,
            total_output=Decimal("1800"),
            defect_rate=Decimal("3.50"),
            completed_orders=14,
            total_orders=20,
            oee_estimate=Decimal("78.00"),
        ),
        AggregatedKPI(
            period_from=recent - timedelta(days=5),
            period_to=recent,
            production_line=None,
            total_output=Decimal("1650"),
            defect_rate=Decimal("4.50"),
            completed_orders=12,
            total_orders=20,
            oee_estimate=Decimal("76.00"),
        ),
        # Old record — should be excluded from 30-day window
        AggregatedKPI(
            period_from=old,
            period_to=old + timedelta(days=7),
            production_line="Line-A",
            total_output=Decimal("500"),
            defect_rate=Decimal("10.00"),
            completed_orders=3,
            total_orders=10,
            oee_estimate=Decimal("50.00"),
        ),
    ]
    for r in records:
        session.add(r)
    await session.commit()
    return records


@pytest_asyncio.fixture
async def sample_order_snapshots(session):
    """
    Insert 8 OrderSnapshot rows with snapshot_date = today - 5 days.

    Line-A:
      - 2 completed on-time (actual_end <= planned_end)
      - 1 completed delayed by 2h
      - 1 in_progress

    Line-B:
      - 1 completed on-time
      - 1 completed delayed by 5h
      - 1 planned
      - 1 cancelled

    All datetime values are timezone.utc aware.
    """
    today = date.today()
    snap = today - timedelta(days=5)
    base_dt = datetime(today.year, today.month, today.day, 14, 0, 0, tzinfo=timezone.utc)

    records = [
        # --- Line-A ---
        # completed, on-time
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product A",
            target_quantity=Decimal("500"),
            actual_quantity=Decimal("490"),
            unit_of_measure="kg",
            status="completed",
            production_line="Line-A",
            planned_start=base_dt - timedelta(hours=8),
            planned_end=base_dt,
            actual_start=base_dt - timedelta(hours=8),
            actual_end=base_dt - timedelta(minutes=30),
            snapshot_date=snap,
        ),
        # completed, on-time
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product A",
            target_quantity=Decimal("400"),
            actual_quantity=Decimal("400"),
            unit_of_measure="kg",
            status="completed",
            production_line="Line-A",
            planned_start=base_dt - timedelta(hours=6),
            planned_end=base_dt + timedelta(hours=2),
            actual_start=base_dt - timedelta(hours=6),
            actual_end=base_dt + timedelta(hours=1),
            snapshot_date=snap,
        ),
        # completed, delayed by 2 hours
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product B",
            target_quantity=Decimal("300"),
            actual_quantity=Decimal("280"),
            unit_of_measure="kg",
            status="completed",
            production_line="Line-A",
            planned_start=base_dt - timedelta(hours=4),
            planned_end=base_dt + timedelta(hours=4),
            actual_start=base_dt - timedelta(hours=4),
            actual_end=base_dt + timedelta(hours=6),  # +2h delay
            snapshot_date=snap,
        ),
        # in_progress — should not count in downtime
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product B",
            target_quantity=Decimal("200"),
            actual_quantity=Decimal("100"),
            unit_of_measure="kg",
            status="in_progress",
            production_line="Line-A",
            planned_start=base_dt - timedelta(hours=2),
            planned_end=base_dt + timedelta(hours=6),
            actual_start=base_dt - timedelta(hours=2),
            actual_end=None,
            snapshot_date=snap,
        ),
        # --- Line-B ---
        # completed, on-time
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product C",
            target_quantity=Decimal("600"),
            actual_quantity=Decimal("600"),
            unit_of_measure="kg",
            status="completed",
            production_line="Line-B",
            planned_start=base_dt - timedelta(hours=8),
            planned_end=base_dt,
            actual_start=base_dt - timedelta(hours=8),
            actual_end=base_dt,
            snapshot_date=snap,
        ),
        # completed, delayed by 5 hours
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product C",
            target_quantity=Decimal("700"),
            actual_quantity=Decimal("650"),
            unit_of_measure="kg",
            status="completed",
            production_line="Line-B",
            planned_start=base_dt - timedelta(hours=6),
            planned_end=base_dt + timedelta(hours=2),
            actual_start=base_dt - timedelta(hours=6),
            actual_end=base_dt + timedelta(hours=7),  # +5h delay
            snapshot_date=snap,
        ),
        # planned
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product D",
            target_quantity=Decimal("300"),
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
        # cancelled
        OrderSnapshot(
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Product D",
            target_quantity=Decimal("100"),
            actual_quantity=Decimal("0"),
            unit_of_measure="kg",
            status="cancelled",
            production_line="Line-B",
            planned_start=base_dt - timedelta(hours=10),
            planned_end=base_dt - timedelta(hours=2),
            actual_start=None,
            actual_end=None,
            snapshot_date=snap,
        ),
    ]
    for r in records:
        session.add(r)
    await session.commit()
    return records


# ---------------------------------------------------------------------------
# OEE summary tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_oee_summary_returns_all_lines(session, sample_kpi_records):
    """Should return one item per production_line group (including NULL)."""
    service = GroupManagerDashboardService(db=session)
    result = await service.get_oee_summary(period_days=30)

    assert isinstance(result, OEESummaryResponse)
    assert len(result.lines) == 3


@pytest.mark.asyncio
async def test_get_oee_summary_ranked_best_first(session, sample_kpi_records):
    """Lines must be sorted descending by avg_oee."""
    service = GroupManagerDashboardService(db=session)
    result = await service.get_oee_summary(period_days=30)

    # Line-A (avg 82.5) should be first
    assert result.lines[0].production_line == "Line-A"
    oees = [item.avg_oee for item in result.lines]
    assert oees == sorted(oees, reverse=True)


@pytest.mark.asyncio
async def test_get_oee_summary_vs_target_correct(session, sample_kpi_records):
    """vs_target_pct = avg_oee - 75.0."""
    service = GroupManagerDashboardService(db=session)
    result = await service.get_oee_summary(period_days=30)

    line_a = next(l for l in result.lines if l.production_line == "Line-A")
    # avg = (85 + 80) / 2 = 82.5 → vs_target = 82.5 - 75.0 = 7.5
    assert line_a.vs_target_pct == Decimal("7.50")

    line_b = next(l for l in result.lines if l.production_line == "Line-B")
    # avg = (70 + 65) / 2 = 67.5 → vs_target = 67.5 - 75.0 = -7.5
    assert line_b.vs_target_pct == Decimal("-7.50")


@pytest.mark.asyncio
async def test_get_oee_summary_trend_has_data_points(session, sample_kpi_records):
    """Each line should have correct data_points count and matching trend list."""
    service = GroupManagerDashboardService(db=session)
    result = await service.get_oee_summary(period_days=30)

    line_a = next(l for l in result.lines if l.production_line == "Line-A")
    assert line_a.data_points == 2
    assert len(line_a.trend) == 2


@pytest.mark.asyncio
async def test_get_oee_summary_filters_by_period(session, sample_kpi_records):
    """Old record (100 days ago) must not be counted in 30-day window."""
    service = GroupManagerDashboardService(db=session)
    result = await service.get_oee_summary(period_days=30)

    # Line-A has 2 recent + 1 old; only 2 should appear
    line_a = next(l for l in result.lines if l.production_line == "Line-A")
    assert line_a.data_points == 2


@pytest.mark.asyncio
async def test_get_oee_summary_empty_returns_empty_list(session):
    """No KPI records → empty lines list with correct defaults."""
    service = GroupManagerDashboardService(db=session)
    result = await service.get_oee_summary(period_days=30)

    assert isinstance(result, OEESummaryResponse)
    assert result.lines == []
    assert result.oee_target == Decimal("75.0")


# ---------------------------------------------------------------------------
# Plan execution tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_plan_execution_calculates_fulfillment(session, sample_order_snapshots):
    """fulfillment_pct == actual_quantity / target_quantity * 100."""
    service = GroupManagerDashboardService(db=session)
    today = date.today()
    result = await service.get_plan_execution(today - timedelta(days=10), today)

    assert isinstance(result, PlanExecutionResponse)
    assert len(result.lines) == 2

    for line_item in result.lines:
        if line_item.target_quantity > 0:
            expected = (
                line_item.actual_quantity / line_item.target_quantity * 100
            ).quantize(Decimal("0.01"))
            assert line_item.fulfillment_pct == expected


@pytest.mark.asyncio
async def test_get_plan_execution_status_counts_are_correct(session, sample_order_snapshots):
    """Status counts per line must match inserted fixture data."""
    service = GroupManagerDashboardService(db=session)
    today = date.today()
    result = await service.get_plan_execution(today - timedelta(days=10), today)

    line_a = next(l for l in result.lines if l.production_line == "Line-A")
    assert line_a.orders_completed == 3
    assert line_a.orders_in_progress == 1
    assert line_a.orders_planned == 0
    assert line_a.orders_cancelled == 0

    line_b = next(l for l in result.lines if l.production_line == "Line-B")
    assert line_b.orders_completed == 2
    assert line_b.orders_planned == 1
    assert line_b.orders_cancelled == 1


@pytest.mark.asyncio
async def test_get_plan_execution_empty_returns_zero_totals(session):
    """Future date range with no data → empty lines, zero totals."""
    service = GroupManagerDashboardService(db=session)
    future = date.today() + timedelta(days=100)
    result = await service.get_plan_execution(future, future + timedelta(days=30))

    assert isinstance(result, PlanExecutionResponse)
    assert result.lines == []
    assert result.total_target == Decimal("0")
    assert result.total_actual == Decimal("0")
    assert result.overall_fulfillment_pct == Decimal("0.00")


# ---------------------------------------------------------------------------
# Downtime ranking tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_downtime_ranking_calculates_delay_hours(session, sample_order_snapshots):
    """Line-B (5h) must rank before Line-A (2h); exact values match."""
    service = GroupManagerDashboardService(db=session)
    today = date.today()
    result = await service.get_downtime_ranking(today - timedelta(days=10), today)

    assert isinstance(result, DowntimeRankingResponse)
    assert len(result.lines) == 2

    # Worst-first: Line-B (5h) before Line-A (2h)
    assert result.lines[0].production_line == "Line-B"
    assert result.lines[0].total_delay_hours == Decimal("5.0000")
    assert result.lines[1].production_line == "Line-A"
    assert result.lines[1].total_delay_hours == Decimal("2.0000")


@pytest.mark.asyncio
async def test_get_downtime_ranking_excludes_non_completed(session, sample_order_snapshots):
    """in_progress/planned/cancelled orders must not affect delay totals."""
    service = GroupManagerDashboardService(db=session)
    today = date.today()
    result = await service.get_downtime_ranking(today - timedelta(days=10), today)

    for line_item in result.lines:
        # delayed_orders can only be <= total_completed
        assert line_item.total_completed >= line_item.delayed_orders
        # Line-A: 3 completed, 1 delayed
        if line_item.production_line == "Line-A":
            assert line_item.total_completed == 3
            assert line_item.delayed_orders == 1
        # Line-B: 2 completed, 1 delayed
        if line_item.production_line == "Line-B":
            assert line_item.total_completed == 2
            assert line_item.delayed_orders == 1


@pytest.mark.asyncio
async def test_get_downtime_ranking_empty_returns_zero_totals(session):
    """Future date range with no data → empty lines, zero grand totals."""
    service = GroupManagerDashboardService(db=session)
    future = date.today() + timedelta(days=100)
    result = await service.get_downtime_ranking(future, future + timedelta(days=30))

    assert isinstance(result, DowntimeRankingResponse)
    assert result.lines == []
    assert result.total_delay_hours == Decimal("0")
    assert result.total_delayed_orders == 0
