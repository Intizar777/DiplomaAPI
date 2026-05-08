"""
Line Master Dashboard schemas for shift-level production views.
"""
from datetime import date as date_type
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class ShiftItem(BaseModel):
    """
    Summary of one shift's production and quality metrics.
    """
    shift: str = Field(description="Shift identifier (e.g., 'Shift 1', 'Shift 2')")
    lot_count: int = Field(description="Number of production lots in shift")
    total_quantity: Decimal = Field(description="Total production quantity (kg/liters)")
    approved_count: int = Field(description="Number of approved lots")
    defect_count: int = Field(description="Number of lots with quality issues")
    defect_rate: Decimal = Field(description="Defect rate as percentage (0-100)")

    model_config = ConfigDict(from_attributes=True)


class ShiftProgressResponse(BaseModel):
    """
    Response: Current shift progress for a production date.
    """
    date: date_type = Field(description="Production date")
    shifts: List["ShiftItem"] = Field(description="Shift-level summaries")
    total_quantity: Decimal = Field(description="Total quantity across all shifts")
    total_lots: int = Field(description="Total lots across all shifts")

    model_config = ConfigDict(from_attributes=True)


class ShiftComparisonPeriod(BaseModel):
    """
    Single shift data point for comparison across periods.
    """
    date: date_type = Field(description="Production date")
    shift: Optional[str] = Field(default=None, description="Shift identifier, or None if aggregated daily")
    total_quantity: Decimal = Field(description="Total production quantity")
    lot_count: int = Field(description="Number of lots")
    defect_count: int = Field(description="Number of defective lots")

    model_config = ConfigDict(from_attributes=True)


class ShiftComparisonResponse(BaseModel):
    """
    Response: Comparison of shifts over a date range.
    """
    period_from: date_type = Field(description="Start of comparison period")
    period_to: date_type = Field(description="End of comparison period")
    shifts: List["ShiftComparisonPeriod"] = Field(description="Shift-level data for comparison")

    model_config = ConfigDict(from_attributes=True)


class DefectItem(BaseModel):
    """
    Quality parameter defect statistics.
    """
    parameter_name: str = Field(description="Quality parameter (e.g., 'acidity', 'moisture')")
    total_tests: int = Field(description="Total tests for this parameter")
    failed_tests: int = Field(description="Number of tests that failed spec")
    fail_rate: Decimal = Field(description="Failure rate as percentage (0-100)")

    model_config = ConfigDict(from_attributes=True)


class DefectSummaryResponse(BaseModel):
    """
    Response: Summary of quality defects by parameter over a period.
    """
    period_from: date_type = Field(description="Start of analysis period")
    period_to: date_type = Field(description="End of analysis period")
    total_defects: int = Field(description="Total number of failed tests")
    items: List["DefectItem"] = Field(description="Defect breakdown by parameter")

    model_config = ConfigDict(from_attributes=True)
