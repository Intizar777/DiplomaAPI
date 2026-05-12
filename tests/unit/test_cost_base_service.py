"""
Unit tests for CostBaseService.
"""
import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CostBase, KPIConfig
from app.services import CostBaseService


@pytest.fixture
def cost_base_service() -> CostBaseService:
    """Fixture for CostBaseService."""
    return CostBaseService()


@pytest.mark.asyncio
async def test_create_cost_base_returns_dict(cost_base_service: CostBaseService, session: AsyncSession):
    """Test creating a cost base returns a dictionary with correct fields."""
    product_id = str(uuid4())
    result = await cost_base_service.create_or_update_cost_base(
        db=session,
        product_id=product_id,
        raw_material_cost=Decimal("50.0"),
        labor_cost_per_hour=Decimal("500.0"),
        depreciation_monthly=Decimal("10000.0"),
        period_from=date(2026, 1, 1),
        period_to=date(2026, 12, 31),
    )

    assert "id" in result
    assert result["product_id"] == product_id
    assert result["raw_material_cost"] == Decimal("50.0")
    assert result["labor_cost_per_hour"] == Decimal("500.0")
    assert result["depreciation_monthly"] == Decimal("10000.0")
    assert result["period_from"] == "2026-01-01"
    assert result["period_to"] == "2026-12-31"


@pytest.mark.asyncio
async def test_create_global_cost_base_with_null_product_id(cost_base_service: CostBaseService, session: AsyncSession):
    """Test creating a global cost base (NULL product_id)."""
    result = await cost_base_service.create_or_update_cost_base(
        db=session,
        product_id=None,
        raw_material_cost=Decimal("45.0"),
        labor_cost_per_hour=Decimal("450.0"),
        depreciation_monthly=Decimal("9000.0"),
        period_from=date(2026, 1, 1),
        period_to=None,
    )

    assert "id" in result
    assert result["product_id"] is None
    assert result["period_to"] is None


@pytest.mark.asyncio
async def test_get_cost_base_returns_latest_active(cost_base_service: CostBaseService, session: AsyncSession):
    """Test getting cost base returns latest active record."""
    product_id = uuid4()

    # Create two cost bases for the same product
    cost_base_1 = CostBase(
        product_id=product_id,
        raw_material_cost=Decimal("40.0"),
        labor_cost_per_hour=Decimal("400.0"),
        depreciation_monthly=Decimal("8000.0"),
        period_from=date(2026, 1, 1),
        period_to=date(2026, 6, 30),
    )
    cost_base_2 = CostBase(
        product_id=product_id,
        raw_material_cost=Decimal("55.0"),
        labor_cost_per_hour=Decimal("550.0"),
        depreciation_monthly=Decimal("11000.0"),
        period_from=date(2026, 7, 1),
        period_to=None,
    )
    session.add_all([cost_base_1, cost_base_2])
    await session.commit()

    # Get as of mid-year (should return first cost base)
    result = await cost_base_service.get_cost_base(
        db=session,
        product_id=str(product_id),
        as_of_date=date(2026, 3, 15),
    )
    assert result is not None
    assert result.raw_material_cost == Decimal("40.0")

    # Get as of later date (should return second cost base)
    result = await cost_base_service.get_cost_base(
        db=session,
        product_id=str(product_id),
        as_of_date=date(2026, 9, 15),
    )
    assert result is not None
    assert result.raw_material_cost == Decimal("55.0")


@pytest.mark.asyncio
async def test_get_all_cost_bases_returns_paginated(cost_base_service: CostBaseService, session: AsyncSession):
    """Test getting all cost bases with pagination."""
    product_id = uuid4()

    # Create multiple cost bases
    for i in range(5):
        cost_base = CostBase(
            product_id=product_id,
            raw_material_cost=Decimal(f"{40 + i * 5}.0"),
            labor_cost_per_hour=Decimal(f"{400 + i * 50}.0"),
            depreciation_monthly=Decimal(f"{8000 + i * 1000}.0"),
            period_from=date(2026, 1 + i, 1),
            period_to=None,
        )
        session.add(cost_base)
    await session.commit()

    result = await cost_base_service.get_all_cost_bases(
        db=session,
        product_id=str(product_id),
        offset=0,
        limit=3,
    )

    assert result["total"] == 5
    assert result["offset"] == 0
    assert result["limit"] == 3
    assert len(result["items"]) == 3


@pytest.mark.asyncio
async def test_set_kpi_config_creates_new(cost_base_service: CostBaseService, session: AsyncSession):
    """Test setting a new KPI config."""
    result = await cost_base_service.set_kpi_config(
        db=session,
        key="market_total_volume_tonnes",
        value=Decimal("1000000.0"),
        description="Total market volume in tonnes",
        updated_by="admin",
    )

    assert "id" in result
    assert result["key"] == "market_total_volume_tonnes"
    assert result["value"] == Decimal("1000000.0")
    assert result["description"] == "Total market volume in tonnes"
    assert result["updated_by"] == "admin"


@pytest.mark.asyncio
async def test_set_kpi_config_updates_existing(cost_base_service: CostBaseService, session: AsyncSession):
    """Test setting an existing KPI config updates it."""
    # Create initial config
    await cost_base_service.set_kpi_config(
        db=session,
        key="ebitda_target_million_rub",
        value=Decimal("150.0"),
        description="EBITDA target",
        updated_by="admin1",
    )

    # Update the config
    result = await cost_base_service.set_kpi_config(
        db=session,
        key="ebitda_target_million_rub",
        value=Decimal("160.0"),
        description="Updated EBITDA target",
        updated_by="admin2",
    )

    assert result["value"] == Decimal("160.0")
    assert result["description"] == "Updated EBITDA target"
    assert result["updated_by"] == "admin2"


@pytest.mark.asyncio
async def test_get_kpi_config_returns_value(cost_base_service: CostBaseService, session: AsyncSession):
    """Test getting a KPI config returns the value."""
    await cost_base_service.set_kpi_config(
        db=session,
        key="test_key",
        value=Decimal("123.45"),
    )

    result = await cost_base_service.get_kpi_config(db=session, key="test_key")

    assert result == Decimal("123.45")


@pytest.mark.asyncio
async def test_get_kpi_config_returns_none_if_not_found(cost_base_service: CostBaseService, session: AsyncSession):
    """Test getting non-existent KPI config returns None."""
    result = await cost_base_service.get_kpi_config(db=session, key="nonexistent_key")

    assert result is None


@pytest.mark.asyncio
async def test_get_all_kpi_configs_returns_paginated(cost_base_service: CostBaseService, session: AsyncSession):
    """Test getting all KPI configs with pagination."""
    # Create multiple configs
    for i in range(5):
        await cost_base_service.set_kpi_config(
            db=session,
            key=f"config_{i}",
            value=Decimal(f"{100 + i * 10}.0"),
        )

    result = await cost_base_service.get_all_kpi_configs(
        db=session,
        offset=0,
        limit=3,
    )

    assert result["total"] == 5
    assert result["offset"] == 0
    assert result["limit"] == 3
    assert len(result["items"]) == 3
