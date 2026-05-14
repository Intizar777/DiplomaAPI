"""
Integration tests for Phase 2 KPI endpoints.
"""
import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AggregatedKPI,
    QualityResult,
    SaleRecord,
    KPIConfig,
)


@pytest.mark.asyncio
async def test_get_line_productivity_endpoint(client: AsyncClient, session: AsyncSession):
    """Test GET /api/production/kpi/line-productivity returns valid response."""
    # Create sample data
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

    response = await client.get(
        "/api/production/kpi/line-productivity",
        params={
            "from_date": "2026-05-01",
            "to_date": "2026-05-01",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "period" in data
    assert "unit" in data


@pytest.mark.asyncio
async def test_get_scrap_percentage_endpoint(client: AsyncClient, session: AsyncSession):
    """Test GET /api/production/kpi/scrap-percentage returns valid response."""
    # Create sample quality results
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
    ]
    session.add_all(results)
    await session.commit()

    response = await client.get(
        "/api/production/kpi/scrap-percentage",
        params={
            "from_date": "2026-05-01",
            "to_date": "2026-05-01",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "scrap_percentage" in data
    assert "rejected_tests" in data
    assert "total_tests" in data
    assert "target" in data


@pytest.mark.asyncio
async def test_set_kpi_config_endpoint(client: AsyncClient, session: AsyncSession):
    """Test POST /api/production/kpi-config sets KPI config."""
    payload = {
        "key": "market_total_volume_tonnes",
        "value": 1000000.0,
        "description": "Total market volume",
        "updated_by": "admin",
    }

    response = await client.post(
        "/api/production/kpi-config",
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["key"] == "market_total_volume_tonnes"
    assert Decimal(str(data["value"])) == Decimal("1000000.0")


@pytest.mark.asyncio
async def test_get_kpi_config_endpoint(client: AsyncClient, session: AsyncSession):
    """Test GET /api/production/kpi-config/{key} retrieves config."""
    # First, set a config
    config = KPIConfig(
        key="test_config_key",
        value=Decimal("12345.0"),
        description="Test config",
    )
    session.add(config)
    await session.commit()

    response = await client.get(
        "/api/production/kpi-config/test_config_key",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "test_config_key"
    assert Decimal(str(data["value"])) == Decimal("12345.0")


@pytest.mark.asyncio
async def test_get_nonexistent_kpi_config_returns_404(client: AsyncClient, session: AsyncSession):
    """Test GET /api/production/kpi-config/{key} returns 404 for nonexistent key."""
    response = await client.get(
        "/api/production/kpi-config/nonexistent_key",
    )

    assert response.status_code == 404
