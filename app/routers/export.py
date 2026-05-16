"""
Dashboard export routes — generate Excel/Word reports for each dashboard role.
"""
from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.dashboard_export_service import DashboardExportService

router = APIRouter(prefix="/api/v1/export", tags=["Export"])

_MIME = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _response(data: bytes, fmt: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([data]),
        media_type=_MIME[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}.{fmt}"'},
    )


async def get_service(db: AsyncSession = Depends(get_db)) -> DashboardExportService:
    return DashboardExportService(db)


@router.get("/gm", summary="Экспорт отчёта Group Manager (Excel/Word)")
async def export_gm(
    fmt: Literal["xlsx", "docx"] = Query(default="xlsx", alias="format", description="Формат файла: xlsx или docx"),
    period_days: int = Query(default=30, ge=1, le=365, description="Период для OEE (дни)."),
    date_from: Optional[date] = Query(default=None, description="Начало периода для плана/простоев (YYYY-MM-DD)."),
    date_to: Optional[date] = Query(default=None, description="Конец периода (YYYY-MM-DD)."),
    service: DashboardExportService = Depends(get_service),
) -> StreamingResponse:
    """
    Скачать аналитический отчёт Group Manager.

    Excel содержит 3 листа: OEE по линиям, Выполнение плана, Простои.
    Каждая строка подсвечена цветом и содержит столбец «Вывод».

    Word содержит аналитический текст с выводами и рекомендациями.
    """
    today = date.today()
    df = date_from or (today - timedelta(days=period_days))
    dt = date_to or today
    data = await service.export_gm(fmt, period_days, df, dt)
    return _response(data, fmt, f"report_gm_{today}")


@router.get("/finance", summary="Экспорт отчёта Finance Manager (Excel/Word)")
async def export_finance(
    fmt: Literal["xlsx", "docx"] = Query(default="xlsx", alias="format", description="Формат файла: xlsx или docx"),
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Начало периода (YYYY-MM-DD).",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="Конец периода (YYYY-MM-DD).",
    ),
    service: DashboardExportService = Depends(get_service),
) -> StreamingResponse:
    """
    Скачать аналитический отчёт Finance Manager.

    Excel содержит 3 листа: Разбивка продаж, Тренд выручки, Топ продукты.
    Word содержит аналитический текст с выводами и рекомендациями.
    """
    data = await service.export_finance(fmt, date_from, date_to)
    return _response(data, fmt, f"report_finance_{date.today()}")


@router.get("/qe", summary="Экспорт отчёта Quality Engineer (Excel/Word)")
async def export_qe(
    fmt: Literal["xlsx", "docx"] = Query(default="xlsx", alias="format", description="Формат файла: xlsx или docx"),
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Начало периода (YYYY-MM-DD).",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="Конец периода (YYYY-MM-DD).",
    ),
    service: DashboardExportService = Depends(get_service),
) -> StreamingResponse:
    """
    Скачать аналитический отчёт Quality Engineer.

    Excel содержит 3 листа: Тренды параметров, Анализ партий, Pareto дефектов.
    Word содержит аналитический текст с выводами и рекомендациями.
    """
    data = await service.export_qe(fmt, date_from, date_to)
    return _response(data, fmt, f"report_qe_{date.today()}")


@router.get("/line-master", summary="Экспорт отчёта Line Master (Excel/Word)")
async def export_line_master(
    fmt: Literal["xlsx", "docx"] = Query(default="xlsx", alias="format", description="Формат файла: xlsx или docx"),
    production_date: date = Query(
        default_factory=date.today,
        description="Дата для прогресса смен (YYYY-MM-DD).",
    ),
    date_from: date = Query(
        default_factory=lambda: date.today() - timedelta(days=7),
        description="Начало периода для сравнения/дефектов (YYYY-MM-DD).",
    ),
    date_to: date = Query(
        default_factory=date.today,
        description="Конец периода (YYYY-MM-DD).",
    ),
    service: DashboardExportService = Depends(get_service),
) -> StreamingResponse:
    """
    Скачать аналитический отчёт Line Master.

    Excel содержит 3 листа: Прогресс смен, Сравнение смен, Сводка дефектов.
    Word содержит аналитический текст с выводами и рекомендациями.
    """
    data = await service.export_line_master(fmt, production_date, date_from, date_to)
    return _response(data, fmt, f"report_line_master_{date.today()}")
