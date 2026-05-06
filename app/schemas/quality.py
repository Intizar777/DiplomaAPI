"""
Quality API schemas.
"""
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class QualityParameterStats(BaseModel):
    """Quality statistics by parameter."""
    in_spec_percent: Decimal = Field(description="Percentage within specification")
    tests_count: int


class QualitySummaryResponse(BaseModel):
    """Quality summary response."""
    average_quality: Decimal = Field(description="Average quality score %")
    approved_count: int
    rejected_count: int
    pending_count: int
    defect_rate: Decimal = Field(description="Overall defect rate %")
    by_parameter: Dict[str, QualityParameterStats] = Field(
        description="Stats by quality parameter"
    )
    period_from: date
    period_to: date
    
    class Config:
        from_attributes = True


class DefectTrendPoint(BaseModel):
    """Single defect trend point."""
    trend_date: date
    defect_rate: Decimal
    rejected_count: int
    total_tests: int


class DefectTrendsResponse(BaseModel):
    """Defect trends response."""
    trends: List[DefectTrendPoint]
    period_from: date
    period_to: date
    
    class Config:
        from_attributes = True


class QualityLotItem(BaseModel):
    """Quality lot item."""
    lot_number: str
    product_id: str
    product_name: Optional[str]
    decision: str  # approved, rejected, pending
    test_date: date
    parameters_tested: int
    parameters_passed: int
    
    class Config:
        from_attributes = True


class QualityLotsResponse(BaseModel):
    """Quality lots response."""
    lots: List[QualityLotItem]
    total: int
    approved_count: int
    rejected_count: int
    pending_count: int
    period_from: date
    period_to: date
    
    class Config:
        from_attributes = True
