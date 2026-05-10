"""
Unit tests for gateway client.

Tests focus on:
- Authentication (login, token refresh)
- Domain-specific request methods
- Error handling (401, timeout, connection errors)
- Retry logic on token expiration
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from decimal import Decimal

from app.services.gateway_client import GatewayClient, GatewayAuthError, GatewayError
from app.config import settings


@pytest_asyncio.fixture
async def gateway_client() -> GatewayClient:
    """Create a GatewayClient instance for testing."""
    client = GatewayClient()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_gateway_client_initializes_with_base_url(gateway_client):
    """Test that client initializes with correct base URL from settings."""
    assert gateway_client.base_url == settings.gateway_url.rstrip("/")
    assert gateway_client.token is None


@pytest.mark.asyncio
async def test_gateway_client_login_success(gateway_client):
    """Test successful authentication."""
    with patch.object(gateway_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        # json() returns dict directly (not awaited in httpx)
        mock_response.json = MagicMock(return_value={"accessToken": "test-token-123"})
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        token = await gateway_client.login()

        assert token == "test-token-123"
        assert gateway_client.token == "test-token-123"
        assert gateway_client.token_acquired_at is not None
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_gateway_client_login_failure_bad_credentials(gateway_client):
    """Test login failure with bad credentials."""
    with patch.object(gateway_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid credentials"
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        with pytest.raises(GatewayAuthError):
            await gateway_client.login()


@pytest.mark.asyncio
async def test_gateway_client_login_timeout(gateway_client):
    """Test login timeout handling."""
    import httpx

    with patch.object(gateway_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_get_client.return_value = mock_client

        with pytest.raises(GatewayAuthError, match="Login timeout"):
            await gateway_client.login()


@pytest.mark.asyncio
async def test_gateway_client_login_connection_error(gateway_client):
    """Test login connection error handling."""
    import httpx

    with patch.object(gateway_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.ConnectError("Connection refused")
        mock_get_client.return_value = mock_client

        with pytest.raises(GatewayAuthError, match="Login connect error"):
            await gateway_client.login()


@pytest.mark.asyncio
async def test_gateway_client_ensure_token_returns_existing(gateway_client):
    """Test that _ensure_token returns existing token without login."""
    gateway_client.token = "existing-token"

    token = await gateway_client._ensure_token()

    assert token == "existing-token"


@pytest.mark.asyncio
async def test_gateway_client_request_includes_bearer_auth(gateway_client):
    """Test that _request includes Authorization header with Bearer token."""
    gateway_client.token = "test-token"

    with patch.object(gateway_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_client.request.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = await gateway_client._request("GET", "/endpoint")

        # Verify Bearer token in headers
        call_kwargs = mock_client.request.call_args[1]
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["Authorization"] == "Bearer test-token"


@pytest.mark.asyncio
async def test_gateway_client_request_success(gateway_client):
    """Test successful request."""
    gateway_client.token = "test-token"

    with patch.object(gateway_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        # json() returns dict directly (not awaited in httpx)
        mock_response.json = MagicMock(return_value={"sales": [{"id": 1, "amount": 100}]})
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await gateway_client._request("GET", "/sales")

        assert result["sales"] is not None
        assert len(result["sales"]) == 1


@pytest.mark.asyncio
async def test_gateway_client_request_retry_on_401(gateway_client):
    """Test that 401 triggers re-login and retry."""
    with patch.object(gateway_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()

        # First call returns 401, second call returns 200
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json = MagicMock(return_value={"data": "success"})

        mock_client.request = AsyncMock(side_effect=[mock_response_401, mock_response_200])

        mock_login_response = MagicMock()
        mock_login_response.status_code = 200
        mock_login_response.json = MagicMock(return_value={"accessToken": "new-token"})
        mock_client.post = AsyncMock(return_value=mock_login_response)
        mock_get_client.return_value = mock_client

        result = await gateway_client._request("GET", "/endpoint")

        # Should have called request twice (original + retry)
        assert mock_client.request.call_count == 2
        # Should have called post once (for login)
        assert mock_client.post.called


@pytest.mark.asyncio
async def test_gateway_client_get_kpi_calls_request(gateway_client):
    """Test that get_kpi calls _request with correct parameters."""
    from datetime import date

    with patch.object(gateway_client, '_request') as mock_request:
        mock_request.return_value = {
            "totalOutput": 1000,
            "defectRate": 2.5,
            "completedOrders": 50,
            "totalOrders": 100,
            "oeeEstimate": 0.75
        }

        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)

        result = await gateway_client.get_kpi(start_date, end_date)

        assert result.totalOutput == 1000
        mock_request.assert_called_once()
        # Verify endpoint
        call_args = mock_request.call_args
        assert "/kpi" in call_args[0][1]


@pytest.mark.asyncio
async def test_gateway_client_get_sales_calls_request(gateway_client):
    """Test that get_sales calls _fetch_all_pages with correct parameters."""
    from uuid import uuid4

    with patch.object(gateway_client, '_fetch_all_pages') as mock_fetch:
        sale_id = str(uuid4())
        product_id = str(uuid4())
        customer_id = str(uuid4())

        mock_fetch.return_value = [{
            "id": sale_id,
            "externalId": "SALE-001",
            "productId": product_id,
            "customerId": customer_id,
            "quantity": 100,
            "amount": 5000,
            "saleDate": "2026-01-01T00:00:00Z",
            "region": "РФ",
            "channel": "retail"
        }]

        result = await gateway_client.get_sales()

        assert len(result.sales) == 1
        assert result.sales[0].amount == 5000
        mock_fetch.assert_called_once()


@pytest.mark.asyncio
async def test_gateway_client_get_orders_calls_request(gateway_client):
    """Test that get_orders calls _fetch_all_pages with correct parameters."""
    from uuid import uuid4
    from datetime import datetime

    with patch.object(gateway_client, '_fetch_all_pages') as mock_fetch:
        order_id = str(uuid4())
        product_id = str(uuid4())
        line_id = str(uuid4())

        mock_fetch.return_value = [{
            "id": order_id,
            "externalOrderId": "ORD-001",
            "productId": product_id,
            "targetQuantity": 100,
            "actualQuantity": 100,
            "status": "completed",
            "productionLineId": line_id,
            "plannedStart": "2026-01-01T00:00:00Z",
            "plannedEnd": "2026-01-05T00:00:00Z",
            "actualStart": "2026-01-01T00:00:00Z",
            "actualEnd": "2026-01-05T00:00:00Z"
        }]

        result = await gateway_client.get_orders()

        assert len(result.orders) == 1
        assert result.orders[0].status == "completed"
        mock_fetch.assert_called_once()


@pytest.mark.asyncio
async def test_gateway_client_get_quality_calls_request(gateway_client):
    """Test that get_quality returns QualityResponse."""
    result = await gateway_client.get_quality()
    # Result should be QualityResponse instance with results
    assert hasattr(result, 'results')
    assert isinstance(result.results, list)
    assert hasattr(result, 'total')
    assert isinstance(result.total, int)


@pytest.mark.asyncio
async def test_gateway_client_get_products_calls_request(gateway_client):
    """Test that get_products returns ProductsResponse."""
    result = await gateway_client.get_products()
    # Result should be ProductsResponse instance with products
    assert hasattr(result, 'products')
    assert isinstance(result.products, list)
    assert hasattr(result, 'total')
    assert isinstance(result.total, int)


@pytest.mark.asyncio
async def test_gateway_client_request_handles_server_error(gateway_client):
    """Test handling of 5xx server errors."""
    gateway_client.token = "test-token"

    with patch.object(gateway_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.request.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Should raise an error on 500
        with pytest.raises(GatewayError):
            await gateway_client._request("GET", "/endpoint")


@pytest.mark.asyncio
async def test_gateway_client_request_handles_timeout(gateway_client):
    """Test handling of request timeouts."""
    import httpx

    gateway_client.token = "test-token"

    with patch.object(gateway_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.TimeoutException("Request timeout")
        mock_get_client.return_value = mock_client

        with pytest.raises(GatewayError):
            await gateway_client._request("GET", "/endpoint")


@pytest.mark.asyncio
async def test_gateway_client_close_is_noop(gateway_client):
    """Test that close is a no-op (client is created per-request)."""
    # Should not raise and should not fail
    await gateway_client.close()
    # No assertion needed — close is intentionally a no-op


@pytest.mark.asyncio
async def test_gateway_client_retry_logic_respects_max_retries(gateway_client):
    """Test that retry logic respects max_retries setting."""
    gateway_client.token = "test-token"

    with patch.object(gateway_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        # All requests fail with timeout
        mock_client.request.side_effect = Exception("Always fails")
        mock_get_client.return_value = mock_client

        with pytest.raises(GatewayError):
            await gateway_client._request("GET", "/endpoint", max_retries=2)

        # Should have tried 2 times
        assert mock_client.request.call_count == 2
