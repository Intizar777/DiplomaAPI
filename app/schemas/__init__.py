"""
Pydantic schemas for API requests/responses.
"""
from app.schemas.common import PaginationParams, PaginatedResponse, DateRangeParams
from app.schemas.kpi import KPICurrentResponse, KPIHistoryResponse, KPICompareResponse
from app.schemas.sales import (
    SalesSummaryResponse,
    SalesTrendsResponse,
    TopProductsResponse,
    SalesRegionsResponse,
)
from app.schemas.orders import (
    OrderStatusSummaryResponse,
    OrderListResponse,
    OrderDetailResponse,
)
from app.schemas.quality import (
    QualitySummaryResponse,
    DefectTrendsResponse,
    QualityLotsResponse,
)
from app.schemas.sync import SyncStatusResponse, SyncTriggerResponse

__all__ = [
    # Common
    "PaginationParams",
    "PaginatedResponse",
    "DateRangeParams",
    # KPI
    "KPICurrentResponse",
    "KPIHistoryResponse",
    "KPICompareResponse",
    # Sales
    "SalesSummaryResponse",
    "SalesTrendsResponse",
    "TopProductsResponse",
    "SalesRegionsResponse",
    # Orders
    "OrderStatusSummaryResponse",
    "OrderListResponse",
    "OrderDetailResponse",
    # Quality
    "QualitySummaryResponse",
    "DefectTrendsResponse",
    "QualityLotsResponse",
    # Sync
    "SyncStatusResponse",
    "SyncTriggerResponse",
]
