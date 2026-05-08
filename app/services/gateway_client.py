"""
HTTP client for Gateway API communication with auto-auth.
"""
import asyncio
import time
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from app.config import settings
from app.utils.logging_utils import log_data_flow
import structlog

logger = structlog.get_logger()


class GatewayError(Exception):
    """Gateway API error."""
    pass


class GatewayAuthError(GatewayError):
    """Gateway authentication error."""
    pass


class GatewayClient:
    """Client for communicating with Gateway API with automatic auth."""
    
    def __init__(self):
        self.base_url = settings.gateway_url.rstrip("/")
        self.token: Optional[str] = None
        self.token_acquired_at: Optional[datetime] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        # Create a new client each time to avoid connection pool issues
        timeout = httpx.Timeout(
            connect=settings.gateway_timeout_connect,
            read=settings.gateway_timeout_read,
            write=10.0,
            pool=10.0
        )
        
        client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            follow_redirects=True
        )
        logger.info(
            "gateway_client_initialized",
            base_url=self.base_url,
            timeout_connect=settings.gateway_timeout_connect,
            timeout_read=settings.gateway_timeout_read,
            max_retries=settings.gateway_max_retries
        )
        return client
    
    async def close(self):
        """Close HTTP client (no-op since client is created per-request)."""
        # No-op since we create a new client for each request
        pass
    
    async def login(self) -> str:
        """
        Authenticate with Gateway via POST /auth/login.
        Returns access token.
        """
        client = await self._get_client()
        
        start_time = time.perf_counter()
        
        logger.info(
            "gateway_auth_login_start",
            email=settings.gateway_auth_email,
            base_url=self.base_url
        )
        
        try:
            response = await client.post(
                "/auth/login",
                json={
                    "email": settings.gateway_auth_email,
                    "password": settings.gateway_auth_password
                }
            )
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            if response.status_code < 200 or response.status_code >= 300:
                logger.error(
                    "gateway_auth_login_failed",
                    status_code=response.status_code,
                    elapsed_ms=round(elapsed_ms, 2),
                    response_body=response.text[:500]
                )
                raise GatewayAuthError(
                    f"Login failed with status {response.status_code}: {response.text[:200]}"
                )
            
            data = response.json()
            self.token = data.get("accessToken")
            self.token_acquired_at = datetime.now(timezone.utc)
            
            logger.info(
                "gateway_auth_login_success",
                elapsed_ms=round(elapsed_ms, 2),
                has_token=bool(self.token)
            )
            
            if not self.token:
                raise GatewayAuthError("Login succeeded but no accessToken in response")
            
            log_data_flow(
                source="gateway_client",
                target="token_store",
                operation="auth_token_acquired",
                payload_summary={"token_prefix": self.token[:8] + "..."} if self.token else None,
            )
            
            return self.token
            
        except httpx.TimeoutException as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "gateway_auth_login_timeout",
                elapsed_ms=round(elapsed_ms, 2),
                error=str(e)
            )
            raise GatewayAuthError(f"Login timeout: {e}") from e
            
        except httpx.ConnectError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "gateway_auth_login_connect_error",
                elapsed_ms=round(elapsed_ms, 2),
                base_url=self.base_url,
                error=str(e)
            )
            raise GatewayAuthError(f"Login connect error: {e}") from e
    
    async def _ensure_token(self) -> str:
        """Ensure we have a valid token, login if needed."""
        if self.token:
            return self.token
        return await self.login()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
        _is_retry: bool = False
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Gateway with retry logic."""
        max_retries = max_retries or settings.gateway_max_retries
        client = await self._get_client()
        url = f"{self.base_url}{endpoint}"
        
        # Ensure we have a token
        token = await self._ensure_token()
        
        last_exception = None
        
        for attempt in range(1, max_retries + 1):
            start_time = time.perf_counter()
            
            logger.info(
                "gateway_request_attempt",
                attempt=attempt,
                max_retries=max_retries,
                method=method,
                endpoint=endpoint,
                url=url,
                params=params
            )
            
            try:
                headers = {"Authorization": f"Bearer {token}"}
                
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers
                )
                
                # If 401 — try to re-login and retry once
                if response.status_code == 401 and not _is_retry:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    logger.warning(
                        "gateway_token_expired_relogin",
                        attempt=attempt,
                        endpoint=endpoint,
                        elapsed_ms=round(elapsed_ms, 2)
                    )
                    
                    # Re-login to get fresh token
                    token = await self.login()
                    
                    # Retry the request with new token (only once)
                    return await self._request(
                        method=method,
                        endpoint=endpoint,
                        params=params,
                        json_data=json_data,
                        max_retries=1,
                        _is_retry=True
                    )
                
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                response_size = len(response.content)
                
                if 200 <= response.status_code < 300:
                    response_data = response.json()
                    log_data_flow(
                        source="gateway_api",
                        target="gateway_client",
                        operation="http_response",
                        payload_summary={
                            "status_code": response.status_code,
                            "content_type": response.headers.get("content-type"),
                            "response_size": response_size,
                        },
                    )
                    logger.info(
                        "gateway_request_success",
                        attempt=attempt,
                        method=method,
                        endpoint=endpoint,
                        status_code=response.status_code,
                        elapsed_ms=round(elapsed_ms, 2),
                        response_size=response_size,
                        content_type=response.headers.get("content-type")
                    )
                    return response_data
                
                # Non-2xx response
                response.raise_for_status()
                
            except httpx.HTTPStatusError as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                # Don't retry on 4xx errors (except 401 handled above)
                if 400 <= e.response.status_code < 500:
                    logger.error(
                        "gateway_http_error_no_retry",
                        attempt=attempt,
                        method=method,
                        endpoint=endpoint,
                        status_code=e.response.status_code,
                        elapsed_ms=round(elapsed_ms, 2),
                        error=str(e),
                        response_body=e.response.text[:500] if e.response.text else None
                    )
                    raise GatewayError(f"HTTP {e.response.status_code}: {e.response.text[:200]}") from e
                
                # Retry on 5xx errors
                logger.warning(
                    "gateway_http_error_retry",
                    attempt=attempt,
                    method=method,
                    endpoint=endpoint,
                    status_code=e.response.status_code,
                    elapsed_ms=round(elapsed_ms, 2),
                    error=str(e)
                )
                last_exception = e
                
            except httpx.TimeoutException as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                logger.warning(
                    "gateway_timeout_retry",
                    attempt=attempt,
                    method=method,
                    endpoint=endpoint,
                    elapsed_ms=round(elapsed_ms, 2),
                    timeout_connect=settings.gateway_timeout_connect,
                    timeout_read=settings.gateway_timeout_read,
                    error=str(e)
                )
                last_exception = e
                
            except httpx.ConnectError as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                logger.warning(
                    "gateway_connect_retry",
                    attempt=attempt,
                    method=method,
                    endpoint=endpoint,
                    elapsed_ms=round(elapsed_ms, 2),
                    base_url=self.base_url,
                    error=str(e)
                )
                last_exception = e
                
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                logger.warning(
                    "gateway_request_retry",
                    attempt=attempt,
                    method=method,
                    endpoint=endpoint,
                    elapsed_ms=round(elapsed_ms, 2),
                    error_type=type(e).__name__,
                    error=str(e)
                )
                last_exception = e
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries:
                wait_time = min(2 ** attempt, 30)
                logger.info(
                    "gateway_retry_wait",
                    attempt=attempt,
                    wait_seconds=wait_time
                )
                await asyncio.sleep(wait_time)
        
        # All retries exhausted
        logger.error(
            "gateway_request_failed_all_retries",
            method=method,
            endpoint=endpoint,
            max_retries=max_retries,
            last_error=str(last_exception),
            last_error_type=type(last_exception).__name__ if last_exception else None
        )
        
        if last_exception:
            raise GatewayError(f"Failed after {max_retries} attempts: {last_exception}") from last_exception
        
        raise GatewayError("Unknown error")
    
    # Pagination helper
    
    async def _fetch_all_pages(
        self,
        endpoint: str,
        data_key: str,
        base_params: Optional[Dict[str, Any]] = None,
        page_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Fetch all pages from a paginated Gateway endpoint.
        
        If Gateway returns 400 on first paginated request (doesn't support
        offset/limit), falls back to a single non-paginated request.
        
        Args:
            endpoint: API path (e.g. "/production/orders")
            data_key: Key in response containing the array (e.g. "orders")
            base_params: Filter params (from, to, status, etc.)
            page_size: Number of records per page (max 100 for Gateway)
        
        Returns:
            Combined list of all records across all pages.
        """
        base_params = base_params or {}
        all_records: List[Dict[str, Any]] = []
        offset = 0
        page = 0
        pagination_supported = True
        
        while True:
            page += 1
            
            if pagination_supported:
                params = {**base_params, "offset": offset, "limit": page_size}
            else:
                params = dict(base_params)
            
            logger.info(
                "gateway_pagination_fetch",
                endpoint=endpoint,
                page=page,
                offset=offset if pagination_supported else None,
                limit=page_size if pagination_supported else None,
                pagination_supported=pagination_supported
            )
            
            try:
                # Use max_retries=1 on first paginated request for fast 400 detection
                if page == 1 and pagination_supported:
                    response = await self._request("GET", endpoint, params=params, max_retries=1)
                else:
                    response = await self._request("GET", endpoint, params=params)
            except GatewayError as e:
                # If first page fails with 400, Gateway may not support offset/limit
                if page == 1 and "400" in str(e) and pagination_supported:
                    logger.warning(
                        "gateway_pagination_not_supported_fallback",
                        endpoint=endpoint,
                        error=str(e)[:200]
                    )
                    pagination_supported = False
                    # Retry without pagination params
                    response = await self._request("GET", endpoint, params=dict(base_params))
                else:
                    raise
            
            records = response.get(data_key, [])
            
            if not records:
                logger.info(
                    "gateway_pagination_empty_page",
                    endpoint=endpoint,
                    page=page,
                    total_fetched=len(all_records)
                )
                break
            
            all_records.extend(records)
            
            logger.info(
                "gateway_pagination_page_fetched",
                endpoint=endpoint,
                page=page,
                fetched_this_page=len(records),
                total_fetched=len(all_records),
                pagination_supported=pagination_supported
            )
            
            # If pagination not supported, single request returns all data
            if not pagination_supported:
                break
            
            # If we got fewer than page_size, this was the last page
            if len(records) < page_size:
                break
            
            offset += page_size
            
            # Rate limit safety: medium profile = 100 req/10s
            await asyncio.sleep(0.15)
        
        logger.info(
            "gateway_pagination_complete",
            endpoint=endpoint,
            data_key=data_key,
            total_records=len(all_records),
            pages_fetched=page,
            pagination_supported=pagination_supported
        )
        
        log_data_flow(
            source="gateway_api",
            target="gateway_client",
            operation="paginated_fetch_complete",
            records_count=len(all_records),
            payload_summary={
                "endpoint": endpoint,
                "pages": page,
                "pagination_supported": pagination_supported,
            },
        )
        
        return all_records
    
    # Production API methods
    
    async def get_kpi(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        production_line_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get production KPI from Gateway."""
        params = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if production_line_id:
            params["productionLineId"] = production_line_id

        data = await self._request("GET", "/production/kpi", params=params)
        kpi_data = data.get("kpi", []) if isinstance(data, dict) else []
        log_data_flow(
            source="gateway_api",
            target="kpi_service",
            operation="fetch_kpi",
            records_count=len(kpi_data) if isinstance(kpi_data, list) else 1,
        )
        return data
    
    async def get_sales(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get sales data from Gateway (paginated)."""
        params = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if group_by:
            params["groupBy"] = group_by
        
        sales = await self._fetch_all_pages("/production/sales", "sales", params)
        log_data_flow(
            source="gateway_api",
            target="sales_service",
            operation="fetch_sales",
            records_count=len(sales),
        )
        return {"sales": sales}
    
    async def get_sales_summary(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get sales summary from Gateway."""
        params = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if group_by:
            params["groupBy"] = group_by
        
        return await self._request("GET", "/production/sales/summary", params=params)
    
    async def get_orders(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        status: Optional[str] = None,
        production_line: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get production orders from Gateway (paginated)."""
        params = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if status:
            params["status"] = status
        if production_line:
            params["productionLine"] = production_line
        
        orders = await self._fetch_all_pages("/production/orders", "orders", params)
        log_data_flow(
            source="gateway_api",
            target="order_service",
            operation="fetch_orders",
            records_count=len(orders),
        )
        return {"orders": orders}
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get single order details from Gateway."""
        return await self._request("GET", f"/production/orders/{order_id}")
    
    async def get_quality(
        self,
        product_id: Optional[str] = None,
        lot_number: Optional[str] = None,
        decision: Optional[str] = None,
        in_spec: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get quality results from Gateway.

        Note: Gateway /production/quality does NOT support from/to or offset/limit.
        All results are fetched in a single request and filtered locally.
        """
        params = {}
        if product_id:
            params["productId"] = product_id
        if lot_number:
            params["lotNumber"] = lot_number
        if decision:
            params["decision"] = decision
        if in_spec is not None:
            params["inSpec"] = str(in_spec).lower()

        data = await self._request("GET", "/production/quality", params=params)
        quality_data = data.get("quality", []) if isinstance(data, dict) else []
        log_data_flow(
            source="gateway_api",
            target="quality_service",
            operation="fetch_quality",
            records_count=len(quality_data) if isinstance(quality_data, list) else 1,
        )
        return data
    
    async def get_output(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get production output from Gateway (paginated)."""
        params = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        
        outputs = await self._fetch_all_pages("/production/output", "outputs", params)
        log_data_flow(
            source="gateway_api",
            target="output_service",
            operation="fetch_output",
            records_count=len(outputs),
        )
        return {"outputs": outputs}
    
    async def get_products(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get products from Gateway."""
        params = {}
        if category:
            params["category"] = category
        if brand:
            params["brand"] = brand

        data = await self._request("GET", "/production/products", params=params)
        products = data.get("products", []) if isinstance(data, dict) else []
        log_data_flow(
            source="gateway_api",
            target="product_service",
            operation="fetch_products",
            records_count=len(products) if isinstance(products, list) else 1,
        )
        return data
    
    async def get_sensors(
        self,
        production_line: Optional[str] = None,
        parameter_name: Optional[str] = None,
        quality: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get sensor readings from Gateway (paginated)."""
        params = {}
        if production_line:
            params["productionLine"] = production_line
        if parameter_name:
            params["parameterName"] = parameter_name
        if quality:
            params["quality"] = quality
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        
        readings = await self._fetch_all_pages("/production/sensors", "readings", params)
        log_data_flow(
            source="gateway_api",
            target="sensor_service",
            operation="fetch_sensors",
            records_count=len(readings),
        )
        return {"readings": readings}
    
    async def get_inventory(
        self,
        product_id: Optional[str] = None,
        warehouse_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get inventory from Gateway.
        
        Note: Gateway /production/inventory does NOT support offset/limit.
        All inventory is fetched in a single request.
        """
        params = {}
        if product_id:
            params["productId"] = product_id
        if warehouse_code:
            params["warehouseCode"] = warehouse_code
        
        data = await self._request("GET", "/production/inventory", params=params)
        items = data.get("inventory", data.get("items", []))
        log_data_flow(
            source="gateway_api",
            target="inventory_service",
            operation="fetch_inventory",
            records_count=len(items) if isinstance(items, list) else None,
        )
        return data

    # Personnel API methods

    async def get_personnel_locations(self) -> Dict[str, Any]:
        """Get personnel locations from Gateway (paginated)."""
        locations = await self._fetch_all_pages("/personnel/locations", "locations")
        return {"locations": locations}

    async def get_personnel_departments(self) -> Dict[str, Any]:
        """Get personnel departments from Gateway (paginated)."""
        departments = await self._fetch_all_pages("/personnel/departments", "departments")
        return {"departments": departments}

    async def get_personnel_positions(self) -> Dict[str, Any]:
        """Get personnel positions from Gateway (paginated)."""
        positions = await self._fetch_all_pages("/personnel/positions", "positions")
        return {"positions": positions}

    async def get_personnel_production_lines(self) -> Dict[str, Any]:
        """Get personnel production lines from Gateway (paginated)."""
        lines = await self._fetch_all_pages("/production/production-lines", "productionLines")
        return {"productionLines": lines}

    async def get_personnel_workstations(self) -> Dict[str, Any]:
        """Get personnel workstations from Gateway (paginated)."""
        workstations = await self._fetch_all_pages("/personnel/workstations", "workstations")
        return {"workstations": workstations}

    async def get_personnel_employees(self) -> Dict[str, Any]:
        """Get personnel employees from Gateway (paginated)."""
        employees = await self._fetch_all_pages("/personnel/employees", "employees")
        log_data_flow(
            source="gateway_api",
            target="personnel_service",
            operation="fetch_employees",
            records_count=len(employees),
        )
        return {"employees": employees}
