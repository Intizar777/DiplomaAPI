"""
HTTP client for Gateway API communication with auto-auth.
"""
import asyncio
import time
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from pydantic import ValidationError
from app.config import settings
from app.schemas.gateway_responses import (
    LoginResponse, LocationsResponse, DepartmentsResponse, PositionsResponse,
    EmployeesResponse, WorkstationsResponse, ProductionLinesResponse,
    ProductsResponse, OrdersResponse, OrderDetailResponse, OutputsResponse,
    SalesResponse, SalesSummaryResponse, KpiResponse, QualityResponse,
    SensorReadingsResponse, InventoryResponse, UnitsOfMeasureResponse,
    CustomersResponse, WarehousesResponse,
)
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

        If Gateway returns 400 with limit too large, retry with limit=100.
        If Gateway returns 400 on non-paginated request, it doesn't support offset/limit.

        Args:
            endpoint: API path (e.g. "/production/orders")
            data_key: Key in response containing the array (e.g. "orders")
            base_params: Filter params (from, to, status, etc.)
            page_size: Number of records per page (default 1000, will use 100 if too large)

        Returns:
            Combined list of all records across all pages.
        """
        base_params = base_params or {}
        all_records: List[Dict[str, Any]] = []
        offset = 0
        page = 0
        pagination_supported = True
        current_page_size = page_size

        while True:
            page += 1

            if pagination_supported:
                params = {**base_params, "offset": offset, "limit": current_page_size}
            else:
                params = dict(base_params)

            logger.info(
                "gateway_pagination_fetch",
                endpoint=endpoint,
                page=page,
                offset=offset if pagination_supported else None,
                limit=current_page_size if pagination_supported else None,
                pagination_supported=pagination_supported
            )

            try:
                # Use max_retries=1 on first paginated request for fast 400 detection
                if page == 1 and pagination_supported:
                    response = await self._request("GET", endpoint, params=params, max_retries=1)
                else:
                    response = await self._request("GET", endpoint, params=params)
            except GatewayError as e:
                # If first page fails with 400 and limit is too large, retry with limit=100
                if page == 1 and "400" in str(e) and "limit must not be greater than 100" in str(e) and current_page_size > 100:
                    logger.warning(
                        "gateway_pagination_limit_too_large",
                        endpoint=endpoint,
                        requested_limit=current_page_size,
                        retrying_with_limit=100
                    )
                    current_page_size = 100
                    # Retry with smaller limit
                    continue
                # If first page fails with 400 on pagination, Gateway may not support offset/limit
                elif page == 1 and "400" in str(e) and pagination_supported:
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
            
            # Handle both dict-wrapped and direct-array responses
            if isinstance(response, list):
                records = response
            elif isinstance(response, dict):
                records = response.get(data_key, [])
            else:
                records = []
            
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
            
            # If we got fewer than current_page_size, this was the last page
            if len(records) < current_page_size:
                break

            offset += current_page_size
            
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
    ) -> KpiResponse:
        """Get production KPI from Gateway."""
        params = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if production_line_id:
            params["productionLineId"] = production_line_id

        data = await self._request("GET", "/production/kpi", params=params)

        try:
            kpi_response = KpiResponse(**data)
            log_data_flow(
                source="gateway_api",
                target="kpi_service",
                operation="fetch_kpi",
                records_count=1,
            )
            return kpi_response
        except ValidationError as e:
            logger.error(
                "gateway_kpi_validation_error",
                error=str(e),
                raw_data=data
            )
            raise
    
    async def get_sales(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        group_by: Optional[str] = None
    ) -> SalesResponse:
        """Get sales data from Gateway (paginated)."""
        params = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if group_by:
            params["groupBy"] = group_by

        sales = await self._fetch_all_pages("/production/sales", "sales", params)

        try:
            sales_response = SalesResponse(sales=sales, total=len(sales))
            log_data_flow(
                source="gateway_api",
                target="sales_service",
                operation="fetch_sales",
                records_count=len(sales),
            )
            return sales_response
        except ValidationError as e:
            logger.error(
                "gateway_sales_validation_error",
                error=str(e),
                records_count=len(sales)
            )
            raise
    
    async def get_sales_summary(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        group_by: Optional[str] = None
    ) -> SalesSummaryResponse:
        """Get sales summary from Gateway."""
        params = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if group_by:
            params["groupBy"] = group_by

        data = await self._request("GET", "/production/sales/summary", params=params)

        try:
            return SalesSummaryResponse(**data)
        except ValidationError as e:
            logger.error("gateway_sales_summary_validation_error", error=str(e))
            raise
    
    async def get_orders(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        status: Optional[str] = None,
        production_line: Optional[str] = None
    ) -> OrdersResponse:
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

        try:
            orders_response = OrdersResponse(orders=orders, total=len(orders))
            log_data_flow(
                source="gateway_api",
                target="order_service",
                operation="fetch_orders",
                records_count=len(orders),
            )
            return orders_response
        except ValidationError as e:
            logger.error("gateway_orders_validation_error", error=str(e))
            raise
    
    async def get_order(self, order_id: str) -> OrderDetailResponse:
        """Get single order details from Gateway."""
        data = await self._request("GET", f"/production/orders/{order_id}")

        try:
            return OrderDetailResponse(**data)
        except ValidationError as e:
            logger.error("gateway_order_detail_validation_error", error=str(e), order_id=order_id)
            raise
    
    async def get_quality(
        self,
        product_id: Optional[str] = None,
        lot_number: Optional[str] = None,
        decision: Optional[str] = None,
        in_spec: Optional[bool] = None
    ) -> QualityResponse:
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

        # Normalize response format
        if isinstance(data, list):
            normalized = {"results": data}
        elif isinstance(data, dict):
            results = data.get("results", data.get("quality", []))
            normalized = {"results": results, "total": len(results)}
        else:
            normalized = {"results": [], "total": 0}

        try:
            quality_response = QualityResponse(**normalized)
            log_data_flow(
                source="gateway_api",
                target="quality_service",
                operation="fetch_quality",
                records_count=len(normalized["results"]),
            )
            return quality_response
        except ValidationError as e:
            logger.error("gateway_quality_validation_error", error=str(e))
            raise
    
    async def get_output(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> OutputsResponse:
        """Get production output from Gateway (paginated)."""
        params = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()

        outputs = await self._fetch_all_pages("/production/output", "outputs", params)

        try:
            outputs_response = OutputsResponse(outputs=outputs, total=len(outputs))
            log_data_flow(
                source="gateway_api",
                target="output_service",
                operation="fetch_output",
                records_count=len(outputs),
            )
            return outputs_response
        except ValidationError as e:
            logger.error("gateway_output_validation_error", error=str(e))
            raise
    
    async def get_products(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None
    ) -> ProductsResponse:
        """Get products from Gateway."""
        params = {}
        if category:
            params["category"] = category
        if brand:
            params["brand"] = brand

        data = await self._request("GET", "/production/products", params=params)

        # Normalize response format
        if isinstance(data, list):
            normalized = {"products": data, "total": len(data)}
        elif isinstance(data, dict):
            products = data.get("products", [])
            normalized = {"products": products, "total": len(products)}
        else:
            normalized = {"products": [], "total": 0}

        try:
            products_response = ProductsResponse(**normalized)
            log_data_flow(
                source="gateway_api",
                target="product_service",
                operation="fetch_products",
                records_count=len(normalized["products"]),
            )
            return products_response
        except ValidationError as e:
            logger.error("gateway_products_validation_error", error=str(e))
            raise
    
    async def get_sensor_readings(
        self,
        production_line: Optional[str] = None,
        parameter_name: Optional[str] = None,
        quality: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> SensorReadingsResponse:
        """Get sensor readings from Gateway (paginated).

        GET /production/sensors returns {readings: [...], total: N}
        Always includes sensorParameter data in the response.
        """
        params = {"include": "sensorParameter"}
        if production_line:
            params["productionLineId"] = production_line
        if parameter_name:
            params["parameterName"] = parameter_name
        if quality:
            params["quality"] = quality
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()

        readings = await self._fetch_all_pages("/production/sensors", "readings", params)

        try:
            readings_response = SensorReadingsResponse(readings=readings, total=len(readings))
            log_data_flow(
                source="gateway_api",
                target="sensor_service",
                operation="fetch_sensor_readings",
                records_count=len(readings),
            )
            return readings_response
        except ValidationError as e:
            logger.error("gateway_sensor_readings_validation_error", error=str(e))
            raise
    
    async def get_inventory(
        self,
        product_id: Optional[str] = None,
        warehouse_code: Optional[str] = None
    ) -> InventoryResponse:
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

        # Normalize response format
        if isinstance(data, list):
            normalized = {"inventory": data, "total": len(data)}
        elif isinstance(data, dict):
            items = data.get("inventory", data.get("items", []))
            normalized = {"inventory": items, "total": len(items)}
        else:
            normalized = {"inventory": [], "total": 0}

        try:
            inventory_response = InventoryResponse(**normalized)
            log_data_flow(
                source="gateway_api",
                target="inventory_service",
                operation="fetch_inventory",
                records_count=len(normalized["inventory"]),
            )
            return inventory_response
        except ValidationError as e:
            logger.error("gateway_inventory_validation_error", error=str(e))
            raise

    # Personnel API methods

    async def get_personnel_locations(self) -> LocationsResponse:
        """Get personnel locations from Gateway (paginated)."""
        locations = await self._fetch_all_pages("/personnel/locations", "locations")

        try:
            return LocationsResponse(locations=locations, total=len(locations))
        except ValidationError as e:
            logger.error("gateway_locations_validation_error", error=str(e))
            raise

    async def get_personnel_departments(self) -> DepartmentsResponse:
        """Get personnel departments from Gateway (paginated)."""
        departments = await self._fetch_all_pages("/personnel/departments", "departments")

        try:
            return DepartmentsResponse(departments=departments, total=len(departments))
        except ValidationError as e:
            logger.error("gateway_departments_validation_error", error=str(e))
            raise

    async def get_personnel_positions(self) -> PositionsResponse:
        """Get personnel positions from Gateway (paginated)."""
        positions = await self._fetch_all_pages("/personnel/positions", "positions")

        try:
            return PositionsResponse(positions=positions, total=len(positions))
        except ValidationError as e:
            logger.error("gateway_positions_validation_error", error=str(e))
            raise

    async def get_personnel_production_lines(self) -> ProductionLinesResponse:
        """Get personnel production lines from Gateway (paginated)."""
        lines = await self._fetch_all_pages("/production/production-lines", "productionLines")

        try:
            return ProductionLinesResponse(productionLines=lines, total=len(lines))
        except ValidationError as e:
            logger.error("gateway_production_lines_validation_error", error=str(e))
            raise

    async def get_personnel_workstations(self) -> WorkstationsResponse:
        """Get personnel workstations from Gateway (paginated)."""
        workstations = await self._fetch_all_pages("/personnel/workstations", "workstations")

        try:
            return WorkstationsResponse(workstations=workstations, total=len(workstations))
        except ValidationError as e:
            logger.error("gateway_workstations_validation_error", error=str(e))
            raise

    async def get_personnel_employees(self) -> EmployeesResponse:
        """Get personnel employees from Gateway (paginated)."""
        employees = await self._fetch_all_pages("/personnel/employees", "employees")

        try:
            employees_response = EmployeesResponse(employees=employees, total=len(employees))
            log_data_flow(
                source="gateway_api",
                target="personnel_service",
                operation="fetch_employees",
                records_count=len(employees),
            )
            return employees_response
        except ValidationError as e:
            logger.error("gateway_employees_validation_error", error=str(e))
            raise

    # Reference data API methods

    async def get_units_of_measure(self) -> UnitsOfMeasureResponse:
        """Get units of measure from Gateway.

        Gateway returns either a direct array or {data: [...]}.
        """
        data = await self._request("GET", "/production/units-of-measure")

        # Normalize response format
        if isinstance(data, list):
            normalized = {"unitsOfMeasure": data, "total": len(data)}
        elif isinstance(data, dict):
            for key in ("unitsOfMeasure", "units", "data", "items", "list"):
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    normalized = {"unitsOfMeasure": items, "total": len(items)}
                    break
            else:
                # If response is a single object, wrap it
                if "id" in data:
                    normalized = {"unitsOfMeasure": [data], "total": 1}
                else:
                    normalized = {"unitsOfMeasure": [], "total": 0}
        else:
            normalized = {"unitsOfMeasure": [], "total": 0}

        try:
            return UnitsOfMeasureResponse(**normalized)
        except ValidationError as e:
            logger.error("gateway_units_of_measure_validation_error", error=str(e))
            raise

    async def get_sensor_parameters(self) -> Dict[str, Any]:
        """Get sensor parameters from Gateway.

        Note: Standalone endpoint may not exist. Sensor parameters are
        typically embedded in sensor data. Returns empty list with warning.
        """
        try:
            data = await self._request("GET", "/production/sensor-parameters")
            if isinstance(data, list):
                return {"parameters": data}
            if isinstance(data, dict):
                for key in ("sensorParameters", "parameters", "data", "items", "list"):
                    if key in data:
                        return {"parameters": data[key]}
                if "id" in data:
                    return {"parameters": [data]}
            return {"parameters": []}
        except GatewayError as e:
            if "404" in str(e):
                logger.warning(
                    "gateway_sensor_parameters_endpoint_not_found",
                    detail="Sensor parameters endpoint does not exist; parameters will be synced via sensor data"
                )
                return {"parameters": []}
            raise

    async def get_customers(self) -> CustomersResponse:
        """Get customers from Gateway (paginated)."""
        customers = await self._fetch_all_pages("/production/customers", "customers")

        try:
            return CustomersResponse(customers=customers, total=len(customers))
        except ValidationError as e:
            logger.error("gateway_customers_validation_error", error=str(e))
            raise

    async def get_warehouses(self) -> WarehousesResponse:
        """Get warehouses from Gateway (paginated)."""
        warehouses = await self._fetch_all_pages("/production/warehouses", "warehouses")

        try:
            return WarehousesResponse(warehouses=warehouses, total=len(warehouses))
        except ValidationError as e:
            logger.error("gateway_warehouses_validation_error", error=str(e))
            raise

    async def get_batch_inputs(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        order_id: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get batch inputs from Gateway (paginated).

        Note: batch_inputs endpoint doesn't support date filtering (from/to parameters).
        All records are returned regardless of date parameters.
        """
        params = {}
        # Note: batch_inputs endpoint doesn't accept from/to parameters
        if order_id:
            params["orderId"] = order_id
        if product_id:
            params["productId"] = product_id

        items = await self._fetch_all_pages("/production/batch-inputs", "items", params, page_size=100)

        log_data_flow(
            source="gateway_api",
            target="batch_input_service",
            operation="fetch_batch_inputs",
            records_count=len(items),
        )
        return {"items": items, "total": len(items)}

    async def get_downtime_events(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        production_line_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get downtime events from Gateway (paginated)."""
        params = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if production_line_id:
            params["productionLineId"] = production_line_id
        if category:
            params["category"] = category

        items = await self._fetch_all_pages("/production/downtime-events", "items", params, page_size=100)

        log_data_flow(
            source="gateway_api",
            target="downtime_event_service",
            operation="fetch_downtime_events",
            records_count=len(items),
        )
        return {"items": items, "total": len(items)}

    async def get_promo_campaigns(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        channel: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get promo campaigns from Gateway (paginated)."""
        params = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if channel:
            params["channel"] = channel
        if status:
            params["status"] = status

        items = await self._fetch_all_pages("/production/promo-campaigns", "items", params, page_size=100)

        log_data_flow(
            source="gateway_api",
            target="promo_campaign_service",
            operation="fetch_promo_campaigns",
            records_count=len(items),
        )
        return {"items": items, "total": len(items)}

    # Convenience aliases used by initial sync

    async def get_locations(self) -> Dict[str, Any]:
        """Alias for get_personnel_locations."""
        return await self.get_personnel_locations()

    async def get_production_lines(self) -> Dict[str, Any]:
        """Alias for get_personnel_production_lines."""
        return await self.get_personnel_production_lines()

    async def get_departments(self) -> Dict[str, Any]:
        """Alias for get_personnel_departments."""
        return await self.get_personnel_departments()

    async def get_workstations(self) -> Dict[str, Any]:
        """Alias for get_personnel_workstations."""
        return await self.get_personnel_workstations()

    async def get_positions(self) -> Dict[str, Any]:
        """Alias for get_personnel_positions."""
        return await self.get_personnel_positions()

    async def get_employees(self) -> Dict[str, Any]:
        """Alias for get_personnel_employees."""
        return await self.get_personnel_employees()

    async def get_quality_specs(
        self,
        product_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get quality specifications from Gateway (paginated).

        Returns a dict with qualitySpecs list and total count.
        """
        params = {"limit": limit, "offset": offset}
        if product_id:
            params["productId"] = product_id

        specs = await self._fetch_all_pages("/production/quality-specs", "qualitySpecs", params)

        log_data_flow(
            source="gateway_api",
            target="quality_specs_service",
            operation="fetch_quality_specs",
            records_count=len(specs),
        )
        return {"qualitySpecs": specs, "total": len(specs)}
