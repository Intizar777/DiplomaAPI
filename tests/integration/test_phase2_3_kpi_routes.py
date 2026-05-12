"""
Integration tests for Phase 2-3 KPI endpoints.
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
    CostBase,
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
async def test_get_marginality_endpoint(client: AsyncClient, session: AsyncSession):
    """Test GET /api/production/kpi/marginality returns valid response."""
    response = await client.get(
        "/api/production/kpi/marginality",
        params={
            "from_date": "2026-05-01",
            "to_date": "2026-05-01",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "margin_percent" in data
    assert "total_revenue" in data
    assert "material_cost" in data
    assert "margin" in data
    assert "target" in data


@pytest.mark.asyncio
async def test_get_cost_per_kg_endpoint(client: AsyncClient, session: AsyncSession):
    """Test GET /api/production/kpi/cost-per-kg returns valid response."""
    response = await client.get(
        "/api/production/kpi/cost-per-kg",
        params={
            "from_date": "2026-05-01",
            "to_date": "2026-05-01",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "cost_per_kg" in data
    assert "total_cost" in data
    assert "total_output" in data
    assert "period" in data


@pytest.mark.asyncio
async def test_get_ebitda_endpoint(client: AsyncClient, session: AsyncSession):
    """Test GET /api/production/kpi/ebitda returns valid response."""
    response = await client.get(
        "/api/production/kpi/ebitda",
        params={
            "from_date": "2026-05-01",
            "to_date": "2026-05-01",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "ebitda_million_rub" in data
    assert "ebitda_value" in data
    assert "total_revenue" in data
    assert "operating_costs" in data


@pytest.mark.asyncio
async def test_get_market_share_endpoint(client: AsyncClient, session: AsyncSession):
    """Test GET /api/production/kpi/market-share returns valid response."""
    response = await client.get(
        "/api/production/kpi/market-share",
        params={
            "from_date": "2026-05-01",
            "to_date": "2026-05-01",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "market_share_percent" in data
    assert "company_volume_tonnes" in data
    assert "market_total_tonnes" in data


@pytest.mark.asyncio
async def test_create_cost_base_endpoint(client: AsyncClient, session: AsyncSession):
    """Test POST /api/production/cost-bases creates cost base."""
    product_id = str(uuid4())
    payload = {
        "product_id": product_id,
        "raw_material_cost": 50.0,
        "labor_cost_per_hour": 500.0,
        "depreciation_monthly": 10000.0,
        "period_from": "2026-01-01",
        "period_to": "2026-12-31",
    }

    response = await client.post(
        "/api/production/cost-bases",
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["product_id"] == product_id
    assert Decimal(str(data["raw_material_cost"])) == Decimal("50.0")


@pytest.mark.asyncio
async def test_list_cost_bases_endpoint(client: AsyncClient, session: AsyncSession):
    """Test GET /api/production/cost-bases lists cost bases."""
    product_id = uuid4()
    cost_base = CostBase(
        product_id=product_id,
        raw_material_cost=Decimal("50.0"),
        labor_cost_per_hour=Decimal("500.0"),
        depreciation_monthly=Decimal("10000.0"),
        period_from=date(2026, 1, 1),
        period_to=None,
    )
    session.add(cost_base)
    await session.commit()

    response = await client.get(
        "/api/production/cost-bases",
        params={
            "product_id": str(product_id),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0


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
