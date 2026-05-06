"""
Common schemas used across API.
"""
from datetime import date, datetime
from typing import Generic, List, TypeVar, Optional

from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    model_config = {"extra": "ignore"}
    
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(default=100, ge=1, le=500, description="Items per page")


class DateRangeParams(BaseModel):
    """Common date range parameters."""
    model_config = {"extra": "ignore", "populate_by_name": True}
    
    date_from: Optional[date] = Field(default=None, alias="from", description="Start date (ISO format)")
    date_to: Optional[date] = Field(default=None, alias="to", description="End date (ISO format)")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: List[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    limit: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(description="Error type/code")
    message: str = Field(description="Human-readable error message")
    details: Optional[dict] = Field(default=None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Service status")
    version: str = Field(description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
