"""
Group Manager Strategic Dashboard schemas.
"""
from datetime import date as date_type
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class OEEDataPoint(BaseModel):
    """Single OEE data point for a trend sparkline."""

    period_from: date_type = Field(description="Start of the KPI aggregation period.")
    period_to: date_type = Field(description="End of the KPI aggregation period.")
    oee_value: Decimal = Field(description="OEE estimate for this period (0–100, percentage).")

    model_config = ConfigDict(from_attributes=True)


class OEELineItem(BaseModel):
    """OEE summary for a single production line."""

    production_line: Optional[str] = Field(
        default=None,
        description="Production line identifier. NULL means the all-lines aggregate record.",
    )
    avg_oee: Decimal = Field(description="Average OEE across all KPI records in the period (0–100, percentage).")
    vs_target_pct: Decimal = Field(
        description="Difference from 75% target: avg_oee - 75.0. Positive = above target."
    )
    completed_orders: int = Field(description="Sum of completed_orders across all KPI records for this line.")
    total_orders: int = Field(description="Sum of total_orders across all KPI records for this line.")
    avg_defect_rate: Decimal = Field(
        description="Average defect_rate across all KPI records (0–100, percentage)."
    )
    data_points: int = Field(description="Number of AggregatedKPI records used for this line.")
    trend: List[OEEDataPoint] = Field(
        description="Chronological list of OEE data points for sparkline/chart rendering."
    )

    model_config = ConfigDict(from_attributes=True)


class OEESummaryResponse(BaseModel):
    """OEE summary by production line for the Group Manager dashboard."""

    period_days: int = Field(description="Lookback window queried in days (e.g. 7, 30, 90).")
    period_from: date_type = Field(description="Calculated start date (today - period_days).")
    period_to: date_type = Field(description="End date (today).")
    lines: List[OEELineItem] = Field(description="Lines ranked best-to-worst by avg_oee.")
    oee_target: Decimal = Field(
        default=Decimal("75.0"),
        description="OEE target threshold used for vs_target_pct (always 75.0%).",
    )

    model_config = ConfigDict(from_attributes=True)


class PlanExecutionLineItem(BaseModel):
    """Plan vs actual execution summary for a single production line."""

    production_line: Optional[str] = Field(
        default=None,
        description="Production line identifier. NULL = orders without an assigned line.",
    )
    target_quantity: Decimal = Field(
        description="Sum of target_quantity for all order snapshots of this line in the period."
    )
    actual_quantity: Decimal = Field(
        description="Sum of actual_quantity for all order snapshots of this line in the period."
    )
    fulfillment_pct: Decimal = Field(
        description="actual_quantity / target_quantity * 100. Returns 0 if target_quantity is zero."
    )
    orders_planned: int = Field(description="Count of order snapshots with status='planned'.")
    orders_in_progress: int = Field(description="Count of order snapshots with status='in_progress'.")
    orders_completed: int = Field(description="Count of order snapshots with status='completed'.")
    orders_cancelled: int = Field(description="Count of order snapshots with status='cancelled'.")
    total_snapshots: int = Field(description="Total count of order snapshots for this line in the period.")

    model_config = ConfigDict(from_attributes=True)


class PlanExecutionResponse(BaseModel):
    """Plan vs actual execution by production line for the Group Manager dashboard."""

    period_from: date_type = Field(description="Start of the analysis period.")
    period_to: date_type = Field(description="End of the analysis period.")
    lines: List[PlanExecutionLineItem] = Field(
        description="One entry per distinct production_line value (including NULL)."
    )
    total_target: Decimal = Field(description="Grand total of all target_quantity across all lines.")
    total_actual: Decimal = Field(description="Grand total of all actual_quantity across all lines.")
    overall_fulfillment_pct: Decimal = Field(
        description="total_actual / total_target * 100. Returns 0 if total_target is zero."
    )

    model_config = ConfigDict(from_attributes=True)


class DowntimeLineItem(BaseModel):
    """Downtime/delay statistics for a single production line."""

    production_line: Optional[str] = Field(
        default=None,
        description="Production line identifier. NULL = orders without an assigned line.",
    )
    total_delay_hours: Decimal = Field(
        description=(
            "Sum of MAX(0, actual_end - planned_end) in decimal hours "
            "for all completed orders where actual_end > planned_end."
        )
    )
    delayed_orders: int = Field(
        description="Count of completed orders where actual_end > planned_end."
    )
    avg_delay_hours: Decimal = Field(
        description="total_delay_hours / delayed_orders. Returns 0 if no delayed orders."
    )
    total_completed: int = Field(
        description="Count of all completed orders for this line in the period (including on-time)."
    )
    delay_pct: Decimal = Field(
        description="delayed_orders / total_completed * 100. Returns 0 if no completed orders."
    )

    model_config = ConfigDict(from_attributes=True)


class DowntimeRankingResponse(BaseModel):
    """Pareto ranking of production lines by total downtime/delay hours."""

    period_from: date_type = Field(description="Start of the analysis period.")
    period_to: date_type = Field(description="End of the analysis period.")
    lines: List[DowntimeLineItem] = Field(
        description="Lines ranked worst-to-best by total_delay_hours (Pareto order)."
    )
    total_delay_hours: Decimal = Field(description="Sum of total_delay_hours across all lines.")
    total_delayed_orders: int = Field(description="Sum of delayed_orders across all lines.")

    model_config = ConfigDict(from_attributes=True)
