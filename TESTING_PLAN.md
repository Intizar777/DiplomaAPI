# Testing Strategy & Plan

Complete test plan for Dashboard Analytics API with test types, libraries, and priorities.

---

## Test Pyramid Overview

```
        ╱╲
       ╱  ╲  E2E Tests (~5%)
      ╱────╲  - Full API workflows
     ╱      ╲
    ╱────────╲ Integration Tests (~20%)
   ╱          ╲ - Service + real database
  ╱────────────╲ Unit Tests (~75%)
 ╱              ╲ - Service methods, utilities
```

**Total target coverage:** >80% of services and critical paths

---

## Libraries & Tools

| Library | Purpose | Usage |
|---------|---------|-------|
| **pytest** | Test runner | Run all tests |
| **pytest-asyncio** | Async test support | `@pytest.mark.asyncio` for async tests |
| **testcontainers[postgresql]** | Real database isolation | Database fixtures in conftest.py |
| **httpx** (already in requirements) | Sync HTTP client | Gateway client mocking in tests |
| **pytest-httpx** (already in requirements) | Mock httpx responses | Mock external Gateway API calls |
| **faker** | Generate test data | Create realistic product/sales data |

**New packages to add:**
```bash
pip install faker
```

---

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures (database, mocks)
├── __init__.py
│
├── unit/
│   ├── test_kpi_service.py
│   ├── test_sales_service.py
│   ├── test_orders_service.py
│   ├── test_quality_service.py
│   ├── test_inventory_service.py
│   ├── test_product_service.py
│   ├── test_sensor_service.py
│   ├── test_output_service.py
│   ├── test_report_service.py
│   └── test_gateway_client.py
│
├── integration/
│   ├── test_kpi_routes.py
│   ├── test_sales_routes.py
│   ├── test_orders_routes.py
│   ├── test_quality_routes.py
│   ├── test_inventory_routes.py
│   ├── test_products_routes.py
│   ├── test_sensors_routes.py
│   ├── test_output_routes.py
│   ├── test_sync_routes.py
│   └── test_health.py
│
└── e2e/
    ├── test_full_kpi_workflow.py
    ├── test_full_sales_workflow.py
    └── test_sync_workflow.py
```

---

## Unit Tests (~75% of suite)

**What:** Test service methods in isolation with mocked external dependencies

**Library:** pytest + testcontainers (real database, mocked HTTP)

**Test each service's public methods:**

### 1. **test_kpi_service.py** (HIGH PRIORITY)

```python
# Current: kpi_service.py has:
# - get_current_kpi()
# - get_kpi_history()
# - get_kpi_compare()
# - sync_from_gateway()

@pytest.mark.asyncio
async def test_get_current_kpi_returns_latest_values(session):
    """Test fetching current KPI metrics"""

@pytest.mark.asyncio
async def test_get_kpi_history_with_date_range(session):
    """Test KPI history filtering by date range"""

@pytest.mark.asyncio
async def test_get_kpi_compare_calculates_differences(session):
    """Test period-over-period KPI comparison"""

@pytest.mark.asyncio
async def test_sync_kpi_from_gateway_creates_records(session, httpx_mock):
    """Test Gateway sync parses response and stores in DB"""
```

### 2. **test_sales_service.py** (HIGH PRIORITY)

```python
# Current: sales_service.py has:
# - get_sales_summary()
# - get_sales_trends()
# - get_top_products()
# - get_sales_by_region()
# - sync_from_gateway()
# - get_sales_with_product_enrichment()

@pytest.mark.asyncio
async def test_get_sales_summary_aggregates_totals(session):
    """Test sales summary calculation"""

@pytest.mark.asyncio
async def test_get_top_products_with_product_name_join(session):
    """Test product name enrichment via JOIN"""

@pytest.mark.asyncio
async def test_get_sales_trends_time_series(session):
    """Test trend calculation with date grouping"""

@pytest.mark.asyncio
async def test_sync_sales_from_gateway_upserts_records(session, httpx_mock):
    """Test sync handles new and updated records"""
```

### 3. **test_orders_service.py** (MEDIUM PRIORITY)

```python
@pytest.mark.asyncio
async def test_get_order_status_summary_counts_by_status(session):
    """Test order status aggregation"""

@pytest.mark.asyncio
async def test_get_orders_with_filtering(session):
    """Test filtering by date, status, warehouse"""

@pytest.mark.asyncio
async def test_get_order_details_joins_related_data(session):
    """Test fetching full order with line items"""
```

### 4. **test_quality_service.py** (MEDIUM PRIORITY)

```python
@pytest.mark.asyncio
async def test_get_quality_summary_calculates_defect_rate(session):
    """Test defect rate calculation"""

@pytest.mark.asyncio
async def test_get_defect_trends_groups_by_date(session):
    """Test defect trend aggregation"""

@pytest.mark.asyncio
async def test_get_lots_with_lot_details(session):
    """Test lot data with status"""
```

### 5. **test_inventory_service.py** (MEDIUM PRIORITY)

```python
@pytest.mark.asyncio
async def test_get_inventory_levels_with_product_name_join(session):
    """Test inventory enrichment with product names"""

@pytest.mark.asyncio
async def test_get_low_stock_items(session):
    """Test filtering items below threshold"""

@pytest.mark.asyncio
async def test_get_inventory_by_warehouse(session):
    """Test warehouse-level aggregation"""
```

### 6. **test_product_service.py** (LOW PRIORITY - reference table)

```python
@pytest.mark.asyncio
async def test_get_all_products(session):
    """Test fetching product master data"""

@pytest.mark.asyncio
async def test_get_product_by_sku(session):
    """Test product lookup"""
```

### 7. **test_sensor_service.py** (MEDIUM PRIORITY)

```python
@pytest.mark.asyncio
async def test_get_sensor_readings_with_time_range(session):
    """Test IoT sensor data retrieval"""

@pytest.mark.asyncio
async def test_get_sensor_latest_reading(session):
    """Test fetching most recent reading"""
```

### 8. **test_output_service.py** (LOW PRIORITY)

```python
@pytest.mark.asyncio
async def test_get_production_output_summary(session):
    """Test output aggregation"""
```

### 9. **test_report_service.py** (MEDIUM PRIORITY - complex logic)

```python
@pytest.mark.asyncio
async def test_generate_daily_report_aggregates_all_domains(session):
    """Test comprehensive daily report generation"""

@pytest.mark.asyncio
async def test_export_to_excel_creates_valid_file(session):
    """Test Excel export with openpyxl"""
```

### 10. **test_gateway_client.py** (MEDIUM PRIORITY - external integration)

```python
# Current: gateway_client.py has:
# - get(url, params)
# - post(url, data)
# - error handling

@pytest.mark.asyncio
async def test_gateway_get_request_with_auth_header(httpx_mock):
    """Test Bearer token included in request"""

@pytest.mark.asyncio
async def test_gateway_client_retry_on_timeout(httpx_mock):
    """Test timeout handling and retries"""

@pytest.mark.asyncio
async def test_gateway_client_raises_on_invalid_token():
    """Test 401 handling"""
```

---

## Integration Tests (~20% of suite)

**What:** Test routes + services together with real database, mocked external APIs

**Library:** pytest + testcontainers + httpx mocks

**Approach:** Create a TestClient and call actual HTTP endpoints

### 1. **test_kpi_routes.py**

```python
# Use FastAPI TestClient with test database

@pytest.mark.asyncio
async def test_get_kpi_current_endpoint_returns_200(client, session):
    """Test GET /api/v1/kpi/current returns valid schema"""

@pytest.mark.asyncio
async def test_get_kpi_current_with_invalid_date_returns_400(client):
    """Test schema validation rejects invalid dates"""

@pytest.mark.asyncio
async def test_kpi_compare_endpoint_calculates_correctly(client, session):
    """Test comparison logic end-to-end"""
```

### 2. **test_sales_routes.py**

```python
@pytest.mark.asyncio
async def test_get_sales_summary_endpoint(client, session):
    """Test GET /api/v1/sales/summary with real data"""

@pytest.mark.asyncio
async def test_get_top_products_includes_product_name(client, session):
    """Test product enrichment in response"""

@pytest.mark.asyncio
async def test_sales_endpoint_filtering_by_warehouse(client, session):
    """Test query parameter filtering"""
```

### 3. **test_orders_routes.py**

```python
@pytest.mark.asyncio
async def test_get_orders_endpoint(client, session):
    """Test GET /api/v1/orders/list"""

@pytest.mark.asyncio
async def test_get_order_by_id_returns_404_for_missing(client):
    """Test 404 on missing order"""

@pytest.mark.asyncio
async def test_get_order_details_endpoint(client, session):
    """Test GET /api/v1/orders/{id}"""
```

### 4. **test_quality_routes.py**

```python
@pytest.mark.asyncio
async def test_get_quality_summary(client, session):
    """Test GET /api/v1/quality/summary"""

@pytest.mark.asyncio
async def test_get_defect_trends(client, session):
    """Test defect trends endpoint"""
```

### 5. **test_inventory_routes.py**

```python
@pytest.mark.asyncio
async def test_get_inventory_levels(client, session):
    """Test GET /api/v1/inventory/levels"""
```

### 6. **test_products_routes.py**

```python
@pytest.mark.asyncio
async def test_get_products_list(client, session):
    """Test GET /api/v1/products"""
```

### 7. **test_sensors_routes.py**

```python
@pytest.mark.asyncio
async def test_get_sensor_readings(client, session):
    """Test GET /api/v1/sensors/readings"""
```

### 8. **test_output_routes.py**

```python
@pytest.mark.asyncio
async def test_get_output_summary(client, session):
    """Test GET /api/v1/outputs"""
```

### 9. **test_sync_routes.py** (CRITICAL - sync logic)

```python
@pytest.mark.asyncio
async def test_get_sync_status(client):
    """Test GET /api/v1/sync/status"""

@pytest.mark.asyncio
async def test_trigger_sync_endpoint(client, httpx_mock):
    """Test POST /api/v1/sync/trigger with mocked gateway"""

@pytest.mark.asyncio
async def test_sync_updates_database_records(client, session, httpx_mock):
    """Test full sync workflow"""
```

### 10. **test_health.py**

```python
@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(client):
    """Test GET /health"""
```

---

## E2E Tests (~5% of suite)

**What:** Full end-to-end workflows simulating real usage

**Library:** pytest + testcontainers + httpx mocks

**Approach:** Seed database, trigger API calls, verify state changes

### 1. **test_full_kpi_workflow.py**

```python
@pytest.mark.asyncio
async def test_complete_kpi_workflow(client, session, httpx_mock):
    """
    Workflow:
    1. Mock gateway to return KPI data
    2. Trigger /sync/trigger
    3. Verify /kpi/current returns synced data
    4. Test /kpi/compare shows trends
    """
```

### 2. **test_full_sales_workflow.py**

```python
@pytest.mark.asyncio
async def test_complete_sales_analytics_workflow(client, session, httpx_mock):
    """
    Workflow:
    1. Insert products and warehouse data
    2. Mock gateway sales data
    3. Trigger sync
    4. Verify /sales/top-products shows enriched data with product_name
    5. Verify /sales/summary aggregates correctly
    6. Verify filtering by warehouse works
    """
```

### 3. **test_sync_workflow.py**

```python
@pytest.mark.asyncio
async def test_hourly_sync_cron_workflow(client, session, httpx_mock):
    """
    Workflow (note: cron runs hourly, test mocks timing):
    1. Start app (scheduler starts)
    2. Mock gateway responses
    3. Simulate cron trigger
    4. Verify all domains (KPI, Sales, Orders, Quality) sync
    5. Verify /sync/status shows last sync timestamp
    """
```

---

## Test Data & Fixtures

### conftest.py additions needed:

```python
# Already have:
# - test_engine() → PostgreSQL testcontainer
# - session() → AsyncSession

# Need to add:

@pytest.fixture
async def client(test_engine):
    """FastAPI TestClient with test database session"""
    
@pytest.fixture
def httpx_mock(mocker):
    """Mock httpx responses for gateway calls"""

@pytest.fixture
async def sample_products(session):
    """Insert 5 sample products"""
    
@pytest.fixture
async def sample_warehouses(session):
    """Insert 3 sample warehouses"""
    
@pytest.fixture
async def sample_sales_data(session, sample_products, sample_warehouses):
    """Insert 100 sample sales records"""
    
@pytest.fixture
async def sample_kpi_data(session):
    """Insert 30 days of KPI data"""
```

### Faker for realistic data:

```python
from faker import Faker

fake = Faker()
product = Product(
    name=fake.word(),
    sku=fake.lexify('SKU-???'),
    source_system_id=fake.uuid4()
)
```

---

## Testing Libraries Summary

**Current (already in requirements.txt):**
- pytest ✅
- pytest-asyncio ✅
- pytest-httpx ✅
- testcontainers[postgresql] ✅

**Need to add to requirements.txt:**
- faker — for generating realistic test data

```bash
pip install faker
```

---

## Priority & Roadmap

### Phase 1: CRITICAL (finish feat-014)

**Priority:** Unit tests for business logic

- [ ] test_sales_service.py — Complex queries, JOIN logic
- [ ] test_kpi_service.py — Aggregation logic
- [ ] test_gateway_client.py — HTTP mocking, error handling

**Target:** 50% coverage, 20 tests

**Estimated effort:** 4-6 hours

---

### Phase 2: HIGH (week 1-2)

**Priority:** Integration tests for routes

- [ ] test_sales_routes.py
- [ ] test_kpi_routes.py
- [ ] test_orders_routes.py
- [ ] test_quality_routes.py
- [ ] test_sync_routes.py

**Target:** 70% coverage, 40 tests total

**Estimated effort:** 6-8 hours

---

### Phase 3: MEDIUM (week 2-3)

**Priority:** E2E workflows + remaining services

- [ ] test_full_sales_workflow.py
- [ ] test_full_kpi_workflow.py
- [ ] test_inventory_service.py + test_inventory_routes.py
- [ ] test_sensor_service.py + test_sensors_routes.py
- [ ] test_product_service.py

**Target:** 80%+ coverage, 60 tests total

**Estimated effort:** 6-8 hours

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v

# Specific test file
pytest tests/unit/test_sales_service.py -v

# With coverage report
pytest tests/ --cov=app --cov-report=html

# Watch mode (pytest-watch)
ptw tests/
```

---

## Coverage Goals

| Module | Current | Target |
|--------|---------|--------|
| app/services/ | 0% | 85%+ |
| app/routers/ | 0% | 70%+ |
| app/models/ | N/A | N/A (ORM, skip) |
| app/schemas/ | N/A | N/A (validation, skip) |
| **Overall** | **0%** | **>80%** |

---

## Checklist for Implementation

- [ ] Add faker to requirements.txt
- [ ] Update conftest.py with TestClient fixture
- [ ] Create tests/unit/, tests/integration/, tests/e2e/ directories
- [ ] Implement Phase 1 tests (unit tests)
- [ ] Run pytest with coverage: `pytest --cov=app`
- [ ] Update feature_list.json feat-014 (Tests) to "done"
- [ ] Commit with message: "tests: add comprehensive unit and integration test suite"

---

**Last updated:** 2026-05-07
