"""
Health check API routes.
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


class RootResponse(BaseModel):
    """Root endpoint response."""
    name: str
    version: str
    docs: str
    health: str

    model_config = {"json_schema_extra": {"example": {"name": "Dashboard Analytics API", "version": "1.0.0", "docs": "/docs", "health": "/health"}}}


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns service status and performs basic database connectivity check.
    """
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        status = "healthy"
    except Exception:
        status = "degraded"
    
    return HealthResponse(
        status=status,
        version=settings.app_version,
        timestamp=datetime.utcnow()
    )


@router.get("/", response_model=RootResponse)
async def root():
    """Root endpoint with basic info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }
