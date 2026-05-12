"""
OEE (Overall Equipment Effectiveness) schema and response models.
"""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class OEEComponentResponse(BaseModel):
    """Single OEE component metric."""
    component: str = Field(..., description="Component name: 'availability', 'performance', 'quality'")
    value: Decimal = Field(..., ge=0, le=100, description="Component value as percentage (0-100)")
    target: Decimal = Field(default=Decimal("85"), description="Target value as percentage")
    status: str = Field(..., description="Status: 'good' (>target), 'warning' (target-10% to target), 'poor' (<target-10%)")


class OEELineResponse(BaseModel):
    """OEE metrics for a single production line."""
    production_line_id: str = Field(..., description="UUID of production line")
    production_line_name: str = Field(..., description="Name of production line")
    availability: OEEComponentResponse = Field(..., description="Equipment availability (0-100%)")
    performance: OEEComponentResponse = Field(..., description="Production performance (0-100%)")
    quality: OEEComponentResponse = Field(..., description="Quality (0-100%)")
    oee: Decimal = Field(..., ge=0, le=100, description="OEE = Availability × Performance × Quality / 10000")
    target_oee: Decimal = Field(default=Decimal("85"), description="Target OEE value")
    period_from: date
    period_to: date


class OEESummaryResponse(BaseModel):
    """OEE summary across multiple lines."""
    summary_date: date
    lines: list[OEELineResponse] = Field(default_factory=list, description="OEE metrics by line")
    total_oee: Decimal = Field(..., ge=0, le=100, description="Average OEE across all lines")
    lines_above_target: int = Field(..., ge=0, description="Count of lines with OEE >= target")
    lines_below_target: int = Field(..., ge=0, description="Count of lines with OEE < target")
    period_from: date
    period_to: date


class LineCapacityPlanRequest(BaseModel):
    """Request to set/update line capacity plan."""
    production_line_id: str = Field(..., description="UUID of production line")
    planned_hours_per_day: int = Field(..., gt=0, le=24, description="Planned working hours per day (1-24)")
    target_oee_percent: Decimal = Field(default=Decimal("85"), ge=0, le=100, description="Target OEE percentage")
    period_from: date
    period_to: date | None = None


class LineCapacityPlanResponse(BaseModel):
    """Line capacity plan response."""
    id: str
    production_line_id: str
    planned_hours_per_day: int
    target_oee_percent: Decimal
    period_from: date
    period_to: date | None
    created_at: str
    updated_at: str
