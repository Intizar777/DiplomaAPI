"""Regression tests for dashboard export rendering."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from openpyxl import load_workbook

from app.services.dashboard_export_service import DashboardExportService


@pytest.mark.parametrize(
    ("stored_oee", "expected_oee_percent"),
    [
        (Decimal("0.813"), 81.3),
        (Decimal("81.3"), 81.3),
    ],
)
def test_production_overview_excel_normalizes_oee_and_omits_output_status(
    stored_oee: Decimal,
    expected_oee_percent: float,
) -> None:
    service = DashboardExportService(db=None)

    workbook_bytes = service._excel_production_overview(
        kpi={
            "total_output": Decimal("2043658.349"),
            "defect_rate": Decimal("0.033"),
            "completed_orders": 128,
            "total_orders": 185,
            "oee_estimate": stored_oee,
            "change_percent": {"total_output": 0.0, "oee_estimate": 0.0},
        },
        otif={
            "otif_rate": Decimal("0.692"),
            "total_orders": 185,
            "on_time_orders": 141,
            "in_full_quantity_orders": 168,
            "otif_orders": 128,
        },
        orders=SimpleNamespace(
            by_production_line={},
            by_status=SimpleNamespace(planned=0, in_progress=0, completed=0, cancelled=0),
        ),
        shifts={"items": []},
        q_summary=SimpleNamespace(
            average_quality=0,
            defect_rate=Decimal("0"),
            approved_count=0,
            rejected_count=0,
            by_parameter={},
        ),
        q_lots=SimpleNamespace(lots=[]),
        regions=SimpleNamespace(regions=[]),
        sensors={"items": []},
        inventory={"snapshot_date": "2026-06-18", "items": []},
        date_from=date(2026, 5, 19),
        date_to=date(2026, 6, 18),
    )

    workbook = load_workbook(io.BytesIO(workbook_bytes))
    sheet = workbook["KPI и OTIF"]

    assert sheet["D3"].value == "—"
    assert sheet["A3"].fill.fill_type is None
    assert sheet["B4"].value == expected_oee_percent
    assert sheet["D4"].value == "Ниже нормы"
    assert sheet["D5"].value == "Критически"
    assert sheet["D6"].value == "Критически"
    assert sheet["D7"].value == "Критически"
    assert sheet["D8"].value == "Ниже нормы"
