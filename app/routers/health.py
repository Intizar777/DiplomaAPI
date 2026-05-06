"""
Health check API routes.
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


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


@router.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }
