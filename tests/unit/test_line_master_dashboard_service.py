"""
Unit tests for Line Master Dashboard service.

Tests focus on:
- Shift progress aggregation (lot counts, quantities, defects)
- Shift comparison across date ranges
- Defect summary by parameter
- Empty data handling
"""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4
import pytest
import pytest_asyncio

from app.models import ProductionOutput, QualityResult
from app.services.line_master_dashboard_service import LineMasterDashboardService
from app.schemas import (
    ShiftProgressResponse,
    ShiftComparisonResponse,
    DefectSummaryResponse,
)


@pytest_asyncio.fixture
async def sample_output_records(session):
    """Insert sample production output records for a 3-day period."""
    today = date.today()
    records = []
    product_id = uuid4()

    # Day 1: 3 shifts with different quantities
    for shift_num in [1, 2, 3]:
        for lot_num in range(1, 3):  # 2 lots per shift
            output = ProductionOutput(
                order_id=None,
                product_id=product_id,
                product_name="Margarine_500g",
                lot_number=f"LOT-{today}-S{shift_num}-{lot_num}",
                quantity=Decimal(str(100 + shift_num * 10 + lot_num)),
                quality_status="approved",
                production_date=today,
                shift=f"Shift {shift_num}",
                snapshot_date=today,
                event_id=None,
            )
            records.append(output)
            session.add(output)

    # Day 2: 2 shifts with some quantity
    yesterday = today - timedelta(days=1)
    for shift_num in [1, 2]:
        for lot_num in range(1, 2):
            output = ProductionOutput(
                order_id=None,
                product_id=product_id,
                product_name="Margarine_500g",
                lot_number=f"LOT-{yesterday}-S{shift_num}-{lot_num}",
                quantity=Decimal(str(150 + shift_num * 20)),
                quality_status="approved",
                production_date=yesterday,
                shift=f"Shift {shift_num}",
                snapshot_date=yesterday,
                event_id=None,
            )
            records.append(output)
            session.add(output)

    # Day 3: 1 shift
    two_days_ago = today - timedelta(days=2)
    output = ProductionOutput(
        order_id=None,
        product_id=product_id,
        product_name="Margarine_500g",
        lot_number=f"LOT-{two_days_ago}-S1-1",
        quantity=Decimal("200"),
        quality_status="approved",
        production_date=two_days_ago,
        shift="Shift 1",
        snapshot_date=two_days_ago,
        event_id=None,
    )
    records.append(output)
    session.add(output)

    await session.commit()
    return records


@pytest_asyncio.fixture
async def sample_quality_records(session):
    """Insert sample quality result records."""
    today = date.today()
    records = []
    product_id = uuid4()

    # Quality checks for today's lots - some pass, some fail
    lot_keys = [
        f"LOT-{today}-S1-1",
        f"LOT-{today}-S1-2",
        f"LOT-{today}-S2-1",
        f"LOT-{today}-S2-2",
        f"LOT-{today}-S3-1",
        f"LOT-{today}-S3-2",
    ]

    for idx, lot_key in enumerate(lot_keys):
        # Add 2 quality tests per lot
        for param_idx, param in enumerate(["acidity", "moisture"]):
            in_spec = not (
                idx == 0 and param_idx == 0
            )  # First lot fails acidity test
            decision = "approved" if in_spec else "failed"
            qr = QualityResult(
                lot_number=lot_key,
                product_id=product_id,
                product_name="Margarine_500g",
                parameter_name=param,
                result_value=Decimal(str(5.5 + idx * 0.1)),
                quality_spec_id=None,
                in_spec=in_spec,
                decision=decision,
                test_date=today,
                event_id=None,
            )
            records.append(qr)
            session.add(qr)

    # Quality checks for yesterday - all pass
    yesterday = date.today() - timedelta(days=1)
    lot_keys_yesterday = [f"LOT-{yesterday}-S1-1", f"LOT-{yesterday}-S2-1"]
    for lot_key in lot_keys_yesterday:
        for param in ["acidity", "moisture", "fat_content"]:
            qr = QualityResult(
                lot_number=lot_key,
                product_id=product_id,
                product_name="Margarine_500g",
                parameter_name=param,
                result_value=Decimal("5.5"),
                quality_spec_id=None,
                in_spec=True,
                decision="approved",
                test_date=yesterday,
                event_id=None,
            )
            records.append(qr)
            session.add(qr)

    await session.commit()
    return records


@pytest.mark.asyncio
async def test_get_shift_progress_returns_all_shifts(
    session, sample_output_records
):
    """Test that shift_progress returns all shifts for a given date."""
    service = LineMasterDashboardService(db=session)
    today = date.today()

    result = await service.get_shift_progress(today)

    assert isinstance(result, ShiftProgressResponse)
    assert result.date == today
    assert len(result.shifts) == 3  # 3 shifts on today
    assert result.total_lots == 6  # 2 lots per shift * 3 shifts


@pytest.mark.asyncio
async def test_get_shift_progress_with_quality_defects(
    session, sample_output_records, sample_quality_records
):
    """Test that shift_progress counts defects correctly."""
    service = LineMasterDashboardService(db=session)
    today = date.today()

    result = await service.get_shift_progress(today)

    assert isinstance(result, ShiftProgressResponse)
    # First lot (LOT-{today}-S1-1) has 1 defect, so S1 should have defect_count=1
    shift_1 = next((s for s in result.shifts if s.shift == "Shift 1"), None)
    assert shift_1 is not None
    assert shift_1.defect_count == 1  # One defective lot in Shift 1


@pytest.mark.asyncio
async def test_get_shift_progress_empty_date(session):
    """Test that shift_progress returns empty for date with no data."""
    service = LineMasterDashboardService(db=session)
    future_date = date.today() + timedelta(days=100)

    result = await service.get_shift_progress(future_date)

    assert isinstance(result, ShiftProgressResponse)
    assert result.date == future_date
    assert len(result.shifts) == 0
    assert result.total_lots == 0


@pytest.mark.asyncio
async def test_get_shift_comparison_groups_by_date_and_shift(
    session, sample_output_records
):
    """Test that shift_comparison correctly groups by date and shift."""
    service = LineMasterDashboardService(db=session)
    today = date.today()
    from_date = today - timedelta(days=3)
    to_date = today

    result = await service.get_shift_comparison(from_date, to_date)

    assert isinstance(result, ShiftComparisonResponse)
    assert result.period_from == from_date
    assert result.period_to == to_date
    # We have 3 shifts on today, 2 on yesterday, 1 on day-before-yesterday = 6 items
    assert len(result.shifts) == 6


@pytest.mark.asyncio
async def test_get_shift_comparison_calculates_quantities(
    session, sample_output_records
):
    """Test that shift_comparison aggregates quantities correctly."""
    service = LineMasterDashboardService(db=session)
    today = date.today()
    from_date = today - timedelta(days=1)
    to_date = today

    result = await service.get_shift_comparison(from_date, to_date)

    # Verify at least one shift has positive quantity
    quantities = [s.total_quantity for s in result.shifts]
    assert any(q > 0 for q in quantities)


@pytest.mark.asyncio
async def test_get_defect_summary_aggregates_by_parameter(
    session, sample_quality_records
):
    """Test that defect_summary groups by parameter and counts failures."""
    service = LineMasterDashboardService(db=session)
    today = date.today()
    from_date = today - timedelta(days=1)
    to_date = today

    result = await service.get_defect_summary(from_date, to_date)

    assert isinstance(result, DefectSummaryResponse)
    assert result.period_from == from_date
    assert result.period_to == to_date
    # We have 3 parameters: acidity, moisture, fat_content
    assert len(result.items) >= 2  # At least acidity and moisture


@pytest.mark.asyncio
async def test_get_defect_summary_calculates_fail_rate(
    session, sample_quality_records
):
    """Test that defect_summary calculates failure rates correctly."""
    service = LineMasterDashboardService(db=session)
    today = date.today()
    from_date = today
    to_date = today

    result = await service.get_defect_summary(from_date, to_date)

    assert isinstance(result, DefectSummaryResponse)
    # Find acidity parameter (should have 1 failure out of 6 tests)
    acidity_item = next((item for item in result.items if item.parameter_name == "acidity"), None)
    assert acidity_item is not None
    assert acidity_item.total_tests == 6  # 6 acidity tests (one per lot)
    assert acidity_item.failed_tests == 1  # 1 failed (LOT-{today}-S1-1)
    assert acidity_item.fail_rate == Decimal("16.67")  # 1/6 * 100


@pytest.mark.asyncio
async def test_get_defect_summary_empty_range(session):
    """Test that defect_summary returns empty for date range with no data."""
    service = LineMasterDashboardService(db=session)
    future_date = date.today() + timedelta(days=100)

    result = await service.get_defect_summary(future_date, future_date)

    assert isinstance(result, DefectSummaryResponse)
    assert result.total_defects == 0
    assert len(result.items) == 0
