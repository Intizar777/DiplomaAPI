# Testing Summary: What, How, Libraries

Quick reference for test strategy, test types, and libraries.

---

## Test Types & Coverage

| Type | Count | Coverage | Libraries |
|------|-------|----------|-----------|
| **UNIT** (service methods) | ~30 | 85%+ | pytest, testcontainers, faker |
| **INTEGRATION** (routes + DB) | ~30 | 70%+ | pytest, testcontainers, FastAPI TestClient |
| **E2E** (full workflows) | ~5 | 100% | pytest, testcontainers, httpx mocks |
| **TOTAL** | **~65** | **>80%** | |

---

## Libraries Breakdown

### Core Testing

| Library | Purpose | Already Installed? |
|---------|---------|-------------------|
| **pytest** | Test runner, fixtures | ✅ Yes |
| **pytest-asyncio** | Async test support (`@pytest.mark.asyncio`) | ✅ Yes |
| **pytest-httpx** | Mock httpx responses (gateway calls) | ✅ Yes |

### Database Testing

| Library | Purpose | Already Installed? |
|---------|---------|-------------------|
| **testcontainers[postgresql]** | Real PostgreSQL in Docker per test | ✅ Yes (just added) |
| **psycopg2-binary** | Sync DB connection for testcontainers | ✅ Yes (just added) |
| **SQLAlchemy AsyncSession** | Async DB queries (already imported) | ✅ Yes |

### Test Data

| Library | Purpose | Already Installed? |
|---------|---------|-------------------|
| **faker** | Generate realistic test data | ❌ Just added |

### FastAPI Testing

| Library | Purpose | Already Installed? |
|---------|---------|-------------------|
| **FastAPI TestClient** | Simulate HTTP requests to routes | ✅ Built-in with FastAPI |
| **httpx** | HTTP client for gateway mocking | ✅ Yes (already in requirements) |

---

## Unit Tests: What to Write

### By Service (10 service files)

**Test each service's public methods:**

```
tests/unit/
├── test_kpi_service.py              [HIGH]  - 4-5 tests
├── test_sales_service.py            [HIGH]  - 6-8 tests (complex JOINs)
├── test_orders_service.py           [MED]   - 3-4 tests
├── test_quality_service.py          [MED]   - 4-5 tests
├── test_inventory_service.py        [MED]   - 4-5 tests
├── test_product_service.py          [LOW]   - 2-3 tests (simple reference data)
├── test_sensor_service.py           [MED]   - 3-4 tests
├── test_output_service.py           [LOW]   - 2-3 tests
├── test_report_service.py           [MED]   - 3-4 tests (Excel export)
└── test_gateway_client.py           [MED]   - 4-5 tests (auth, retries, errors)
```

**Total:** ~40 tests

**Example test structure:**

```python
import pytest
from app.services.sales_service import SalesService
from app.models import Product, SalesData

@pytest.mark.asyncio
async def test_get_top_products_returns_sorted_by_quantity(session):
    """ARRANGE: Insert test data"""
    session.add(Product(name="Widget"))
    session.add(SalesData(product_id=1, quantity=100))
    await session.commit()
    
    """ACT: Call service"""
    service = SalesService()
    result = await service.get_top_products(session)
    
    """ASSERT: Verify result"""
    assert len(result) == 1
    assert result[0].name == "Widget"
    assert result[0].quantity == 100
```

---

## Integration Tests: What to Write

### By Route (10 router files)

**Test each route with real database:**

```
tests/integration/
├── test_kpi_routes.py               [HIGH]  - 5-6 tests
├── test_sales_routes.py             [HIGH]  - 6-8 tests
├── test_orders_routes.py            [MED]   - 4-5 tests
├── test_quality_routes.py           [MED]   - 4-5 tests
├── test_inventory_routes.py         [MED]   - 3-4 tests
├── test_products_routes.py          [LOW]   - 2-3 tests
├── test_sensors_routes.py           [MED]   - 3-4 tests
├── test_output_routes.py            [LOW]   - 2-3 tests
├── test_sync_routes.py              [CRIT]  - 5-6 tests (complex)
└── test_health.py                   [LOW]   - 1-2 tests
```

**Total:** ~40 tests

**Example test structure:**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.asyncio
async def test_get_sales_summary_returns_valid_schema(client, session):
    """Test HTTP GET /api/v1/sales/summary"""
    
    # Setup: Insert test data
    session.add(SalesData(...))
    await session.commit()
    
    # Act: Call endpoint
    response = client.get("/api/v1/sales/summary")
    
    # Assert: Verify response
    assert response.status_code == 200
    data = response.json()
    assert "total_amount" in data
    assert "order_count" in data
```

---

## E2E Tests: What to Write

### Full Workflows (3-5 tests)

**Test real end-to-end scenarios:**

```
tests/e2e/
├── test_full_kpi_workflow.py        - Sync → Query → Verify
├── test_full_sales_workflow.py      - Sync → Product enrichment → Trends
├── test_sync_workflow.py            - Hourly cron simulation
└── test_gateway_integration.py      - Mock gateway, sync all domains
```

**Total:** ~5 tests

**Example test structure:**

```python
@pytest.mark.asyncio
async def test_complete_sales_workflow(client, session, httpx_mock):
    """
    End-to-end scenario:
    1. Insert products and warehouses
    2. Mock gateway to return sales data
    3. Call /api/v1/sync/trigger
    4. Verify /api/v1/sales/summary returns synced data
    5. Verify /api/v1/sales/top-products includes product_name
    """
    
    # Setup: Insert master data
    session.add(Product(name="Widget"))
    session.add(Warehouse(name="WH-1"))
    await session.commit()
    
    # Mock: Gateway returns sales
    httpx_mock.add_response(
        method="GET",
        url="http://gateway:3000/api/sales/latest",
        json=[{"product_id": 1, "amount": 100}]
    )
    
    # Act: Trigger sync
    response = client.post("/api/v1/sync/trigger")
    assert response.status_code == 200
    
    # Verify: Check summary is synced
    response = client.get("/api/v1/sales/summary")
    assert response.json()["total_amount"] == 100
    
    # Verify: Check enrichment works
    response = client.get("/api/v1/sales/top-products")
    products = response.json()
    assert products[0]["name"] == "Widget"  # Product name via JOIN
```

---

## Implementation Priority

### Phase 1: CRITICAL (feat-014 completion)

**Start with unit tests for complex services:**

1. ✅ **test_sales_service.py** - JOINs, product enrichment
2. ✅ **test_kpi_service.py** - Aggregation logic
3. ✅ **test_gateway_client.py** - HTTP mocking, auth
4. ✅ **conftest.py** - Fixtures with sample data (products, warehouses)

**Estimated:** 4-6 hours for ~15 tests

**Run:** `pytest tests/unit/ -v`

---

### Phase 2: HIGH (week 1-2)

**Integration tests for critical routes:**

1. test_sales_routes.py
2. test_kpi_routes.py
3. test_sync_routes.py
4. test_orders_routes.py
5. test_quality_routes.py

**Estimated:** 6-8 hours for ~25 tests total

**Run:** `pytest tests/integration/ -v`

---

### Phase 3: MEDIUM (week 2-3)

**Remaining unit tests + E2E workflows:**

1. E2E workflows (sales, KPI, sync)
2. Remaining services (inventory, sensors, product)
3. Coverage reporting

**Estimated:** 6-8 hours for ~65 tests total

**Run:** `pytest tests/ --cov=app`

---

## Quick Start Checklist

- [x] Add faker to requirements.txt
- [ ] Update conftest.py:
  - [ ] Add `client` fixture (FastAPI TestClient)
  - [ ] Add `httpx_mock` fixture
  - [ ] Add `sample_products()`, `sample_warehouses()` fixtures
- [ ] Create directory structure: `tests/unit/`, `tests/integration/`, `tests/e2e/`
- [ ] Write Phase 1 unit tests (15 tests)
- [ ] Run: `pytest tests/unit/ -v`
- [ ] Check coverage: `pytest tests/unit/ --cov=app.services --cov-report=term`

---

## Coverage Commands

```bash
# Coverage for services only
pytest tests/unit/ --cov=app.services --cov-report=term-missing

# Coverage for routes
pytest tests/integration/ --cov=app.routers --cov-report=term-missing

# Full coverage HTML report
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# Coverage minimum enforcement
pytest tests/ --cov=app --cov-fail-under=80
```

---

## Key Testing Patterns

### Pattern 1: Test Service Methods (Unit)

```python
@pytest.mark.asyncio
async def test_service_method(session):
    # Arrange: Insert data
    await session.add(Model(...))
    await session.commit()
    
    # Act: Call service
    result = await service.method(session)
    
    # Assert: Verify
    assert result.field == expected_value
```

### Pattern 2: Test Routes (Integration)

```python
@pytest.mark.asyncio
async def test_route_endpoint(client, session):
    # Setup: Prepare data
    await session.add(Model(...))
    await session.commit()
    
    # Act: Call endpoint
    response = client.get("/api/v1/endpoint")
    
    # Assert: Verify response
    assert response.status_code == 200
    assert response.json()["field"] == expected_value
```

### Pattern 3: Mock External APIs (Unit/Integration)

```python
@pytest.mark.asyncio
async def test_sync_with_mocked_gateway(session, httpx_mock):
    # Mock: Set up HTTP response
    httpx_mock.add_response(
        method="GET",
        url="http://gateway/api/sales",
        json=[{"id": 1, "amount": 100}]
    )
    
    # Act: Call sync
    result = await sync_service.sync_from_gateway(session)
    
    # Assert: Verify DB was updated
    records = await session.query(SalesData).all()
    assert len(records) == 1
```

---

## Summary Table

| Aspect | What | How | Libraries |
|--------|------|-----|-----------|
| **Unit Tests** | Service methods in isolation | Mock external APIs, use real DB | pytest, testcontainers, faker |
| **Integration Tests** | Routes + services with real DB | HTTP calls, verify responses | pytest, FastAPI TestClient, testcontainers |
| **E2E Tests** | Full workflows | Simulate real usage scenarios | pytest, httpx mocks, testcontainers |
| **Test Data** | Realistic sample data | Faker library | faker |
| **Database** | Isolated per test | Testcontainers PostgreSQL | testcontainers |
| **External APIs** | Mock gateway calls | pytest-httpx | pytest-httpx |

---

**Reference:** See TESTING_PLAN.md for detailed test definitions by service/route.

**Last updated:** 2026-05-07
