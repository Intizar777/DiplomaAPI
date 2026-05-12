"""
Unit tests for OEE service.
"""
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ProductionLine,
    DowntimeEvent,
    ProductionOutput,
    QualityResult,
    LineCapacityPlan,
)
from app.services.oee_service import OEEService


@pytest.fixture
def oee_service() -> OEEService:
    """OEE service instance."""
    return OEEService()


@pytest.fixture
async def sample_production_line(session: AsyncSession) -> ProductionLine:
    """Create a sample production line."""
    line = ProductionLine(
        name="Line A",
        code="LINE-A",
        location="Building 1",
        is_active=True,
    )
    session.add(line)
    await session.commit()
    await session.refresh(line)
    return line


@pytest.fixture
async def sample_capacity_plan(
    session: AsyncSession, sample_production_line: ProductionLine
) -> LineCapacityPlan:
    """Create a sample capacity plan."""
    import uuid
    plan = LineCapacityPlan(
        id=uuid.uuid4(),
        production_line_id=sample_production_line.id,
        planned_hours_per_day=16,
        target_oee_percent=Decimal("85"),
        period_from=date(2026, 5, 1),
        period_to=None,
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


@pytest.fixture
async def sample_downtime(
    session: AsyncSession, sample_production_line: ProductionLine
) -> DowntimeEvent:
    """Create a sample downtime event."""
    import uuid
    event = DowntimeEvent(
        id=uuid.uuid4(),
        production_line_id=sample_production_line.id,
        reason="Machine breakdown",
        category="unplanned",
        started_at=datetime(2026, 5, 12, 10, 0),
        ended_at=datetime(2026, 5, 12, 11, 30),
        duration_minutes=90,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


@pytest.fixture
async def sample_output(
    session: AsyncSession, sample_production_line: ProductionLine
) -> ProductionOutput:
    """Create a sample production output."""
    import uuid
    output = ProductionOutput(
        id=uuid.uuid4(),
        order_id=None,
        product_id=uuid.uuid4(),
        product_name="Oil",
        lot_number="LOT-001",
        quantity=Decimal("100.5"),
        quality_status="passed",
        production_date=date(2026, 5, 12),
        shift="Day",
        snapshot_date=date(2026, 5, 12),
    )
    session.add(output)
    await session.commit()
    await session.refresh(output)
    return output


@pytest.fixture
async def sample_quality_result(
    session: AsyncSession,
) -> QualityResult:
    """Create a sample quality result."""
    import uuid
    import uuid as uuid_lib
    result = QualityResult(
        id=uuid_lib.uuid4(),
        lot_number="LOT-001",
        product_id=uuid_lib.uuid4(),
        product_name="Oil",
        parameter_name="Acidity",
        result_value=Decimal("0.5"),
        in_spec=True,
        decision="accepted",
        test_date=date(2026, 5, 12),
    )
    session.add(result)
    await session.commit()
    await session.refresh(result)
    return result


@pytest.mark.asyncio
async def test_get_status_good(oee_service: OEEService) -> None:
    """Test status calculation for good performance."""
    status = oee_service._get_status(Decimal("95"), Decimal("85"))
    assert status == "good"


@pytest.mark.asyncio
async def test_get_status_warning(oee_service: OEEService) -> None:
    """Test status calculation for warning performance."""
    status = oee_service._get_status(Decimal("80"), Decimal("85"))
    assert status == "warning"


@pytest.mark.asyncio
async def test_get_status_poor(oee_service: OEEService) -> None:
    """Test status calculation for poor performance."""
    status = oee_service._get_status(Decimal("70"), Decimal("85"))
    assert status == "poor"


@pytest.mark.asyncio
async def test_calculate_availability_with_downtime(
    session: AsyncSession,
    oee_service: OEEService,
    sample_production_line: ProductionLine,
    sample_capacity_plan: LineCapacityPlan,
    sample_downtime: DowntimeEvent,
) -> None:
    """Test availability calculation with downtime."""
    period_from = date(2026, 5, 12)
    period_to = date(2026, 5, 12)

    availability = await oee_service._calculate_availability(
        session,
        str(sample_production_line.id),
        period_from,
        period_to,
        sample_capacity_plan,
    )

    assert availability.component == "availability"
    assert availability.value < Decimal("100")  # Should be less than 100 due to downtime
    assert 0 <= availability.value <= 100


@pytest.mark.asyncio
async def test_calculate_performance(
    session: AsyncSession,
    oee_service: OEEService,
    sample_production_line: ProductionLine,
    sample_capacity_plan: LineCapacityPlan,
    sample_output: ProductionOutput,
) -> None:
    """Test performance calculation."""
    period_from = date(2026, 5, 12)
    period_to = date(2026, 5, 12)

    performance = await oee_service._calculate_performance(
        session,
        str(sample_production_line.id),
        period_from,
        period_to,
        sample_capacity_plan,
    )

    assert performance.component == "performance"
    assert 0 <= performance.value <= 100


@pytest.mark.asyncio
async def test_calculate_quality_with_accepted(
    session: AsyncSession,
    oee_service: OEEService,
    sample_production_line: ProductionLine,
    sample_quality_result: QualityResult,
) -> None:
    """Test quality calculation with accepted results."""
    period_from = date(2026, 5, 12)
    period_to = date(2026, 5, 12)

    quality = await oee_service._calculate_quality(
        session,
        str(sample_production_line.id),
        period_from,
        period_to,
    )

    assert quality.component == "quality"
    assert quality.value == Decimal("100")  # 100% accepted


@pytest.mark.asyncio
async def test_calculate_oee_for_line(
    session: AsyncSession,
    oee_service: OEEService,
    sample_production_line: ProductionLine,
    sample_capacity_plan: LineCapacityPlan,
) -> None:
    """Test OEE calculation for a single line."""
    period_from = date(2026, 5, 12)
    period_to = date(2026, 5, 12)

    oee_line = await oee_service.calculate_oee_for_line(
        session,
        str(sample_production_line.id),
        period_from,
        period_to,
    )

    assert oee_line.production_line_id == str(sample_production_line.id)
    assert oee_line.production_line_name == "Line A"
    assert oee_line.availability.component == "availability"
    assert oee_line.performance.component == "performance"
    assert oee_line.quality.component == "quality"
    assert 0 <= oee_line.oee <= 100
    assert oee_line.target_oee == Decimal("85")


@pytest.mark.asyncio
async def test_calculate_oee_summary(
    session: AsyncSession,
    oee_service: OEEService,
    sample_production_line: ProductionLine,
    sample_capacity_plan: LineCapacityPlan,
) -> None:
    """Test OEE summary calculation."""
    period_from = date(2026, 5, 12)
    period_to = date(2026, 5, 12)

    summary = await oee_service.calculate_oee_summary(
        session,
        period_from=period_from,
        period_to=period_to,
    )

    assert summary.period_from == period_from
    assert summary.period_to == period_to
    assert len(summary.lines) > 0
    assert summary.lines_above_target >= 0
    assert summary.lines_below_target >= 0
    assert 0 <= summary.total_oee <= 100


@pytest.mark.asyncio
async def test_set_capacity_plan(
    session: AsyncSession,
    oee_service: OEEService,
    sample_production_line: ProductionLine,
) -> None:
    """Test setting a new capacity plan."""
    response = await oee_service.set_capacity_plan(
        session,
        production_line_id=str(sample_production_line.id),
        planned_hours_per_day=18,
        target_oee_percent=Decimal("90"),
        period_from=date(2026, 6, 1),
        period_to=None,
    )

    assert response.production_line_id == str(sample_production_line.id)
    assert response.planned_hours_per_day == 18
    assert response.target_oee_percent == Decimal("90")
    assert response.period_from == date(2026, 6, 1)


@pytest.mark.asyncio
async def test_calculate_oee_for_invalid_line(
    session: AsyncSession,
    oee_service: OEEService,
) -> None:
    """Test OEE calculation for non-existent line."""
    import uuid
    with pytest.raises(ValueError, match="not found"):
        await oee_service.calculate_oee_for_line(
            session,
            production_line_id=str(uuid.uuid4()),
            period_from=date(2026, 5, 12),
            period_to=date(2026, 5, 12),
        )
