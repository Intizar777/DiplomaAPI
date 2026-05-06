"""
Reports API endpoints.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.report_service import ReportService
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/types")
async def get_report_types(
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """Get available report types and formats."""
    service = ReportService(db)
    return await service.get_report_metadata()


@router.post("/generate/{report_type}")
async def generate_report(
    report_type: str,
    format_type: str = Query(default="xlsx", regex="^(csv|xlsx)$"),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    period: str = Query(default="week", regex="^(day|week|month|quarter)$"),
    status: Optional[str] = Query(default=None),
    production_line: Optional[str] = Query(default=None),
    region: Optional[str] = Query(default=None),
    decision: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Generate and download a report.
    
    Available report types:
    - orders: Production orders
    - quality: Quality control results
    - sales: Sales data
    - inventory: Current inventory
    - kpi: Production KPIs
    """
    # Calculate dates if not provided
    if not date_from or not date_to:
        today = date.today()
        if period == "day":
            date_from = today
            date_to = today
        elif period == "week":
            date_from = today - timedelta(days=7)
            date_to = today
        elif period == "month":
            date_from = today.replace(day=1)
            date_to = today
        elif period == "quarter":
            quarter = (today.month - 1) // 3
            date_from = today.replace(month=quarter * 3 + 1, day=1)
            date_to = today
    
    # Build filters
    filters = {}
    if status:
        filters["status"] = status
    if production_line:
        filters["production_line"] = production_line
    if region:
        filters["region"] = region
    if decision:
        filters["decision"] = decision
    
    logger.info(
        "report_generation_request",
        report_type=report_type,
        format_type=format_type,
        date_from=date_from,
        date_to=date_to,
        filters=filters
    )
    
    try:
        service = ReportService(db)
        report_data = await service.generate_report(
            report_type=report_type,
            format_type=format_type,
            date_from=date_from,
            date_to=date_to,
            filters=filters
        )
        
        # Determine content type and filename
        if format_type == "csv":
            media_type = "text/csv; charset=utf-8-sig"
            extension = "csv"
        else:
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        
        filename = f"{report_type}_report_{date_from}_{date_to}.{extension}"
        
        return StreamingResponse(
            iter([report_data]),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except ValueError as e:
        logger.error("report_generation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("report_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/download/{report_type}")
async def download_report(
    report_type: str,
    format_type: str = Query(default="xlsx", regex="^(csv|xlsx)$"),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    period: str = Query(default="week", regex="^(day|week|month|quarter)$"),
    db: AsyncSession = Depends(get_db)
):
    """Download a report (GET endpoint for simple browser links)."""
    return await generate_report(
        report_type=report_type,
        format_type=format_type,
        date_from=date_from,
        date_to=date_to,
        period=period,
        db=db
    )
