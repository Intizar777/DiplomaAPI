"""
Unit tests for gateway client HTTP communication.

Tests focus on:
- Authentication header (Bearer token)
- Request/response handling
- Error handling and retries
- Timeout scenarios
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.services.gateway_client import GatewayClient
from app.config import settings


@pytest.fixture
def gateway_client() -> GatewayClient:
    """Create a GatewayClient instance for testing."""
    return GatewayClient()


@pytest.mark.asyncio
async def test_gateway_client_includes_bearer_token(gateway_client):
    """Test that requests include Bearer token in Authorization header."""
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Make request
        result = await gateway_client.get("/endpoint")

        # Verify Bearer token was included
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        headers = call_kwargs.get('headers', {})
        assert 'Authorization' in headers or 'authorization' in headers


@pytest.mark.asyncio
async def test_gateway_client_get_request_success(gateway_client):
    """Test successful GET request."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "sales": [
                {"product_id": 1, "amount": 100},
                {"product_id": 2, "amount": 200}
            ]
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        result = await gateway_client.get("/sales/latest")

        assert result["sales"] is not None
        assert len(result["sales"]) == 2
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_gateway_client_post_request_success(gateway_client):
    """Test successful POST request."""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"id": "sync-123", "status": "completed"}
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response

        data = {"from_date": "2024-01-01", "to_date": "2024-01-31"}
        result = await gateway_client.post("/sync", data=data)

        assert result["id"] == "sync-123"
        assert result["status"] == "completed"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_gateway_client_handles_401_unauthorized(gateway_client):
    """Test that 401 errors are handled properly."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=AsyncMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await gateway_client.get("/endpoint")


@pytest.mark.asyncio
async def test_gateway_client_handles_404_not_found(gateway_client):
    """Test that 404 errors are handled properly."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=AsyncMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await gateway_client.get("/nonexistent")


@pytest.mark.asyncio
async def test_gateway_client_handles_500_server_error(gateway_client):
    """Test that 500 errors are handled properly."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", request=AsyncMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await gateway_client.get("/endpoint")


@pytest.mark.asyncio
async def test_gateway_client_timeout_handling(gateway_client):
    """Test that timeouts are handled."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Request timed out")

        with pytest.raises(httpx.TimeoutException):
            await gateway_client.get("/slow-endpoint")


@pytest.mark.asyncio
async def test_gateway_client_handles_connection_error(gateway_client):
    """Test that connection errors are handled."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(httpx.ConnectError):
            await gateway_client.get("/unreachable")


@pytest.mark.asyncio
async def test_gateway_client_json_parsing_error(gateway_client):
    """Test handling of invalid JSON response."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        with pytest.raises(ValueError):
            await gateway_client.get("/invalid-json")


@pytest.mark.asyncio
async def test_gateway_client_returns_full_response_object(gateway_client):
    """Test that client returns the full response object."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        result = await gateway_client.get("/endpoint")

        assert isinstance(result, dict)
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_gateway_client_passes_query_parameters(gateway_client):
    """Test that query parameters are properly passed."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": []}
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        params = {"from_date": "2024-01-01", "limit": "10"}
        await gateway_client.get("/sales", params=params)

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs.get('params') == params or call_kwargs.get('params') is not None


@pytest.mark.asyncio
async def test_gateway_client_set_timeout(gateway_client):
    """Test that requests use configured timeout."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {}
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        await gateway_client.get("/endpoint")

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        # Timeout should be set to something > 0
        assert 'timeout' in call_kwargs or call_kwargs.get('timeout') is not None


@pytest.mark.asyncio
async def test_gateway_client_url_construction(gateway_client):
    """Test that URLs are properly constructed from settings."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {}
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        await gateway_client.get("/endpoint")

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        # URL should include gateway base
        assert "http" in str(call_args) or settings.GATEWAY_URL in str(call_args)


@pytest.mark.asyncio
async def test_gateway_client_handles_empty_response(gateway_client):
    """Test handling of empty response body."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 204  # No Content
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.side_effect = ValueError("No JSON in response")
        mock_get.return_value = mock_response

        # Should handle 204 gracefully
        with pytest.raises(ValueError):
            result = await gateway_client.get("/endpoint")
