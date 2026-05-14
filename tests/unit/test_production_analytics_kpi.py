"""
Unit tests for Phase 2-3 KPI methods in ProductionAnalyticsService.
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AggregatedKPI,
    QualityResult,
    SaleRecord,
    BatchInput,
    ProductionOutput,
    DowntimeEvent,
    KPIConfig,
)
from app.services import ProductionAnalyticsService


@pytest.fixture
async def kpi_service(session: AsyncSession) -> ProductionAnalyticsService:
    """Fixture for ProductionAnalyticsService."""
    return ProductionAnalyticsService(session)


@pytest.fixture
async def sample_aggregated_kpi(session: AsyncSession):
    """Fixture for sample aggregated KPI data."""
    kpi = AggregatedKPI(
        period_from=date(2026, 5, 1),
        period_to=date(2026, 5, 1),
        production_line="LINE-001",
        total_output=Decimal("100.000"),
        defect_rate=Decimal("0.01"),
        completed_orders=10,
        total_orders=10,
        oee_estimate=Decimal("0.85"),
        avg_order_completion_time="8h",
    )
    session.add(kpi)
    await session.commit()
    await session.refresh(kpi)
    return kpi


@pytest.fixture
async def sample_quality_results(session: AsyncSession):
    """Fixture for sample quality results."""
    product_id = uuid4()
    results = [
        QualityResult(
            lot_number="LOT001",
            product_id=product_id,
            product_name="Oil Type A",
            parameter_name="Acidity",
            result_value=Decimal("0.5"),
            in_spec=True,
            decision="accepted",
            test_date=date(2026, 5, 1),
        ),
        QualityResult(
            lot_number="LOT002",
            product_id=product_id,
            product_name="Oil Type A",
            parameter_name="Acidity",
            result_value=Decimal("2.5"),
            in_spec=False,
            decision="rejected",
            test_date=date(2026, 5, 1),
        ),
        QualityResult(
            lot_number="LOT003",
            product_id=product_id,
            product_name="Oil Type A",
            parameter_name="Acidity",
            result_value=Decimal("0.6"),
            in_spec=True,
            decision="accepted",
            test_date=date(2026, 5, 1),
        ),
    ]
    session.add_all(results)
    await session.commit()
    return results


# ============ Phase 2 KPI Tests ============


@pytest.mark.asyncio
async def test_get_line_productivity_returns_list(kpi_service: ProductionAnalyticsService, sample_aggregated_kpi):
    """Test line productivity returns data with correct structure."""
    result = await kpi_service.get_line_productivity(
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 1),
    )

    assert "items" in result
    assert "period" in result
    assert "unit" in result
    assert result["unit"] == "tonnes/hour"
    assert len(result["items"]) > 0
    assert "productivity" in result["items"][0]
    assert "target" in result["items"][0]
    assert "status" in result["items"][0]


@pytest.mark.asyncio
async def test_get_line_productivity_calculates_correctly(kpi_service: ProductionAnalyticsService, sample_aggregated_kpi):
    """Test line productivity calculation is correct."""
    result = await kpi_service.get_line_productivity(
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 1),
    )

    item = result["items"][0]
    # 100 tonnes / (16 hours * 1 day) = 6.25 tonnes/hour
    assert item["total_output"] == Decimal("100.000")
    assert item["days"] == 1
    expected_productivity = Decimal("100.000") / (Decimal("16") * 1)
    assert item["productivity"] == expected_productivity


@pytest.mark.asyncio
async def test_get_scrap_percentage_returns_correct_structure(kpi_service: ProductionAnalyticsService, sample_quality_results):
    """Test scrap percentage returns correct structure."""
    result = await kpi_service.get_scrap_percentage(
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 1),
    )

    assert "scrap_percentage" in result
    assert "rejected_tests" in result
    assert "total_tests" in result
    assert "target" in result
    assert "status" in result
    assert result["target"] == Decimal("1.5")


@pytest.mark.asyncio
async def test_get_scrap_percentage_calculates_correctly(kpi_service: ProductionAnalyticsService, sample_quality_results):
    """Test scrap percentage calculation is correct."""
    result = await kpi_service.get_scrap_percentage(
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 1),
    )

    # 1 rejected out of 3 total = 33.33%
    assert result["rejected_tests"] == 1
    assert result["total_tests"] == 3
    expected_scrap = Decimal(1) / Decimal(3) * 100
    assert result["scrap_percentage"] == expected_scrap
