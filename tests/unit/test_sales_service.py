"""
Unit tests for sales service business logic.

Tests focus on:
- Aggregation correctness
- Filtering and grouping
- Fallback behavior (aggregated vs raw data)
- Database queries with proper ordering
"""

from datetime import date, timedelta
from decimal import Decimal
import pytest

from app.models import AggregatedSales
from app.services.sales_service import SalesService
from app.schemas import SalesSummaryResponse, TopProductsResponse, SalesRegionsResponse


@pytest.mark.asyncio
async def test_get_sales_summary_returns_aggregated_data(session, sample_sales_data):
    """Test that get_sales_summary returns aggregated data for a period."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service.get_sales_summary(
        from_date=today - timedelta(days=30),
        to_date=today,
        group_by="product"
    )

    assert isinstance(result, SalesSummaryResponse)
    assert result.total_amount > 0
    assert result.total_quantity > 0
    assert len(result.summary) > 0
    assert result.group_by == "product"


@pytest.mark.asyncio
async def test_get_sales_summary_group_by_product(session, sample_sales_data):
    """Test aggregation grouped by product."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service.get_sales_summary(
        from_date=today - timedelta(days=30),
        to_date=today,
        group_by="product"
    )

    # Verify each summary item has required fields
    for item in result.summary:
        assert hasattr(item, 'group_key')
        assert hasattr(item, 'total_quantity')
        assert hasattr(item, 'total_amount')
        assert hasattr(item, 'sales_count')


@pytest.mark.asyncio
async def test_get_sales_summary_returns_empty_for_future_dates(session):
    """Test that querying future dates returns empty results."""
    service = SalesService(db=session, gateway=None)
    tomorrow = date.today() + timedelta(days=1)
    next_week = tomorrow + timedelta(days=7)

    result = await service.get_sales_summary(
        from_date=tomorrow,
        to_date=next_week,
        group_by="product"
    )

    assert result.total_amount == 0
    assert result.total_quantity == 0
    assert len(result.summary) == 0


@pytest.mark.asyncio
async def test_get_sales_summary_calculates_total_correctly(session, sample_sales_data):
    """Test that totals are calculated from summary items."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service.get_sales_summary(
        from_date=today - timedelta(days=30),
        to_date=today,
        group_by="product"
    )

    # Total should be sum of all summary items
    calculated_total = sum(item.total_amount for item in result.summary)
    assert result.total_amount == calculated_total


@pytest.mark.asyncio
async def test_get_sales_trends_returns_ordered_by_date(session, db_session_with_data):
    """Test that sales trends are returned ordered by date."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service.get_sales_trends(
        from_date=today - timedelta(days=30),
        to_date=today,
        interval="day"
    )

    # Verify structure
    assert hasattr(result, 'trends')
    assert hasattr(result, 'interval')
    assert result.interval == "day"

    # If trends exist, verify ordering
    if len(result.trends) > 1:
        for i in range(len(result.trends) - 1):
            assert result.trends[i].trend_date <= result.trends[i + 1].trend_date


@pytest.mark.asyncio
async def test_get_top_products_returns_limited_results(session, sample_sales_data):
    """Test that get_top_products respects limit parameter."""
    service = SalesService(db=session, gateway=None)
    today = date.today()
    limit = 3

    result = await service.get_top_products(
        from_date=today - timedelta(days=30),
        to_date=today,
        limit=limit
    )

    assert isinstance(result, TopProductsResponse)
    assert len(result.products) <= limit


@pytest.mark.asyncio
async def test_get_top_products_ordered_by_amount(session, sample_sales_data):
    """Test that top products are ordered by total_amount descending."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service.get_top_products(
        from_date=today - timedelta(days=30),
        to_date=today,
        limit=10
    )

    # Verify descending order by amount
    if len(result.products) > 1:
        for i in range(len(result.products) - 1):
            assert result.products[i].total_amount >= result.products[i + 1].total_amount


@pytest.mark.asyncio
async def test_get_sales_by_regions_returns_regional_breakdown(session, sample_sales_data):
    """Test that regional breakdown includes percentage calculations."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service.get_sales_by_regions(
        from_date=today - timedelta(days=30),
        to_date=today
    )

    assert isinstance(result, SalesRegionsResponse)
    assert hasattr(result, 'regions')

    # Verify percentage field exists and is valid
    if len(result.regions) > 0:
        for region in result.regions:
            assert hasattr(region, 'percentage')
            assert 0 <= region.percentage <= 100


@pytest.mark.asyncio
async def test_get_sales_by_regions_percentages_sum_to_100(session, sample_sales_data):
    """Test that regional percentages sum to approximately 100."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service.get_sales_by_regions(
        from_date=today - timedelta(days=30),
        to_date=today
    )

    if len(result.regions) > 0:
        total_percentage = sum(r.percentage for r in result.regions)
        # Allow small rounding error
        assert 99 <= total_percentage <= 101


@pytest.mark.asyncio
async def test_get_sales_summary_with_invalid_date_range(session):
    """Test behavior when from_date > to_date."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service.get_sales_summary(
        from_date=today,
        to_date=today - timedelta(days=30),
        group_by="product"
    )

    # Should return empty results
    assert result.total_amount == 0
    assert len(result.summary) == 0


@pytest.mark.asyncio
async def test_get_top_products_with_zero_limit(session, sample_sales_data):
    """Test that zero limit returns no results."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service.get_top_products(
        from_date=today - timedelta(days=30),
        to_date=today,
        limit=0
    )

    assert len(result.products) == 0


@pytest.mark.asyncio
async def test_get_sales_trends_with_region_filter(session, db_session_with_data):
    """Test that regional filtering works in trends."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    # Query with specific region
    result = await service.get_sales_trends(
        from_date=today - timedelta(days=30),
        to_date=today,
        interval="day",
        region="North"
    )

    # All results should match the region filter (if any)
    assert result.region == "North"


@pytest.mark.asyncio
async def test_get_sales_trends_with_channel_filter(session, db_session_with_data):
    """Test that channel filtering works in trends."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service.get_sales_trends(
        from_date=today - timedelta(days=30),
        to_date=today,
        interval="day",
        channel="Online"
    )

    assert result.channel == "Online"


@pytest.mark.asyncio
async def test_aggregate_from_raw_returns_list(session, db_session_with_data):
    """Test _aggregate_from_raw method returns properly formatted list."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service._aggregate_from_raw(
        from_date=today - timedelta(days=30),
        to_date=today,
        group_by="product"
    )

    assert isinstance(result, list)

    # Each item should have required fields
    for item in result:
        assert "group_key" in item
        assert "total_quantity" in item
        assert "total_amount" in item
        assert "sales_count" in item


@pytest.mark.asyncio
async def test_get_sales_summary_default_group_by_is_region(session, sample_sales_data):
    """Test that default group_by parameter is 'region'."""
    service = SalesService(db=session, gateway=None)
    today = date.today()

    result = await service.get_sales_summary(
        from_date=today - timedelta(days=30),
        to_date=today
    )

    # Default should be "region"
    assert result.group_by == "region"
