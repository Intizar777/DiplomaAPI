"""
Quality Engineer Dashboard schemas.
"""
from datetime import date as date_type
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class TrendDataPoint(BaseModel):
    """Single daily aggregation point for a quality parameter trend."""

    test_date: date_type = Field(description="Date of the aggregation bucket.")
    avg_value: Decimal = Field(description="Average result_value for this day (4dp).")
    test_count: int = Field(description="Total test rows for this day.")
    out_of_spec_count: int = Field(description="Count of rows where in_spec=False for this day.")
    out_of_spec_pct: Decimal = Field(description="out_of_spec_count / test_count * 100 (2dp; 0 if no tests).")
    lower_limit: Optional[Decimal] = Field(default=None, description="Spec lower limit from QualitySpec (None if no spec).")
    upper_limit: Optional[Decimal] = Field(default=None, description="Spec upper limit from QualitySpec (None if no spec).")

    model_config = ConfigDict(from_attributes=True)


class ParameterTrendItem(BaseModel):
    """Trend data for a single quality parameter across the analysis period."""

    parameter_name: str = Field(description="Name of the quality parameter (e.g. pH, viscosity).")
    total_tests: int = Field(description="Total test rows for this parameter in the period.")
    total_out_of_spec: int = Field(description="Total out-of-spec rows for this parameter in the period.")
    overall_out_of_spec_pct: Decimal = Field(description="total_out_of_spec / total_tests * 100 (2dp).")
    trend: List[TrendDataPoint] = Field(description="Daily data points, ascending by date.")

    model_config = ConfigDict(from_attributes=True)


class ParameterTrendsResponse(BaseModel):
    """Parameter-level quality trend response for the Quality Engineer Dashboard."""

    period_from: date_type = Field(description="Start of the analysis period.")
    period_to: date_type = Field(description="End of the analysis period.")
    parameters: List[ParameterTrendItem] = Field(description="One entry per distinct parameter_name.")

    model_config = ConfigDict(from_attributes=True)


class DeviationItem(BaseModel):
    """A single out-of-spec QualityResult row with deviation magnitude."""

    parameter_name: str = Field(description="Quality parameter name.")
    result_value: Decimal = Field(description="Measured result value.")
    lower_limit: Optional[Decimal] = Field(default=None, description="Spec lower limit (None if no spec).")
    upper_limit: Optional[Decimal] = Field(default=None, description="Spec upper limit (None if no spec).")
    deviation_magnitude: Decimal = Field(
        description="Absolute distance from the breached limit (4dp; 0 if limits are None)."
    )

    model_config = ConfigDict(from_attributes=True)


class BatchAnalysisItem(BaseModel):
    """A lot that had at least one out-of-spec result, with deviation details."""

    lot_number: str = Field(description="Lot/batch identifier.")
    product_name: Optional[str] = Field(default=None, description="Product name from ProductionOutput.")
    production_date: Optional[date_type] = Field(default=None, description="Production date from ProductionOutput.")
    shift: Optional[str] = Field(default=None, description="Shift from ProductionOutput.")
    fail_count: int = Field(description="Number of out-of-spec results for this lot.")
    deviations: List[DeviationItem] = Field(description="Per-parameter deviation details.")

    model_config = ConfigDict(from_attributes=True)


class BatchAnalysisResponse(BaseModel):
    """Batch deviation analysis response for the Quality Engineer Dashboard."""

    period_from: date_type = Field(description="Start of the analysis period.")
    period_to: date_type = Field(description="End of the analysis period.")
    lot_count: int = Field(description="Number of lots with at least one deviation.")
    lots: List[BatchAnalysisItem] = Field(description="Deviating lots, sorted ascending by production_date (None last).")

    model_config = ConfigDict(from_attributes=True)


class ParetoItem(BaseModel):
    """One parameter entry in the defect Pareto chart."""

    parameter_name: str = Field(description="Quality parameter name.")
    defect_count: int = Field(description="Number of out-of-spec results for this parameter.")
    total_tests: int = Field(description="Total tests for this parameter in the period.")
    defect_pct: Decimal = Field(description="defect_count / total_tests * 100 (2dp).")
    cumulative_pct: Decimal = Field(
        description="Running cumulative share of total defects ranked by defect_count DESC (2dp)."
    )

    model_config = ConfigDict(from_attributes=True)


class DefectParetoResponse(BaseModel):
    """Defect Pareto chart response for the Quality Engineer Dashboard."""

    period_from: date_type = Field(description="Start of the analysis period.")
    period_to: date_type = Field(description="End of the analysis period.")
    product_id: Optional[UUID] = Field(default=None, description="Product filter applied (None = all products).")
    total_defects: int = Field(description="Grand total of out-of-spec results in the period.")
    parameters: List[ParetoItem] = Field(description="Parameters ranked descending by defect_count.")

    model_config = ConfigDict(from_attributes=True)
