"""Integration tests for include support in production analytics routes."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AggregatedKPI
from app.models.reference import ProductionLine


@pytest.mark.asyncio
async def test_get_kpi_breakdown_include_production_line(client: AsyncClient, session: AsyncSession):
    """GET /api/production/kpi/breakdown supports include=productionLine."""
    line = ProductionLine(
        id=uuid4(),
        code="LINE-001",
        name="Line 1",
        division="Oil",
        is_active=True,
    )
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
    session.add_all([line, kpi])
    await session.commit()

    response = await client.get(
        "/api/production/kpi/breakdown",
        params={
            "from_date": "2026-05-01",
            "to_date": "2026-05-01",
            "group_by": "productionLine",
            "metric": "oeeEstimate",
            "include": "productionLine",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"]
    assert data["items"][0]["production_line"] is not None
