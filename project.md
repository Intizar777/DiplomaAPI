# DiplomaAPI — Complete Project Overview

## Executive Summary

DiplomaAPI is a **FastAPI-based analytics service** that aggregates production KPI, sales, orders, quality, and inventory data from external EFKO microservices. It syncs data hourly via APScheduler, maintains PostgreSQL as the single source of truth, and exposes RESTful endpoints for analytical queries.

**Tech Stack:** FastAPI 0.104+, SQLAlchemy 2.x async, PostgreSQL 14+, Pydantic v2, APScheduler 3.x, structlog (JSON logging), Alembic migrations, pytest + testcontainers.

**Architecture:** Three-layer (Route → Service → Database), async-first, domain-driven, with immutable migrations.

---

## Architecture Overview

### Three-Layer Design

```
┌──────────────────────────────────────────────────┐
│  ROUTE LAYER (Thin Validation)                   │
│  - FastAPI @router endpoints                     │
│  - Pydantic schema validation (request/response) │
│  - Delegates to services, returns JSON           │
│  - 3-5 lines per endpoint                        │
└──────────────┬───────────────────────────────────┘
               │ depends_on
┌──────────────▼───────────────────────────────────┐
│  SERVICE LAYER (All Business Logic)              │
│  - Database queries (SQLAlchemy ORM)             │
│  - Gateway API calls (httpx async client)        │
│  - Data aggregation, filtering, enrichment       │
│  - Structured logging (structlog)                │
│  - Sync methods (hourly via APScheduler)         │
└──────────────┬───────────────────────────────────┘
               │ uses
┌──────────────▼───────────────────────────────────┐
│  DATABASE LAYER (ORM + Persistence)              │
│  - SQLAlchemy 2.x async models                   │
│  - PostgreSQL 14+ (acid transactions, types)     │
│  - Alembic migrations (versioned, immutable)     │
│  - Foreign keys, constraints, indices            │
└──────────────────────────────────────────────────┘
```

**Rationale:**
- **Testability:** Test services without FastAPI/HTTP dependencies
- **Reusability:** Same service can be called from route, cron job, or CLI
- **Clarity:** Business logic in one place (service), know where bugs are
- **Async throughout:** All I/O non-blocking → high concurrency

---

## Domain Architecture

DiplomaAPI organizes around **7 domains**, each representing a business capability:

| Domain | Purpose | Key Tables | Key Endpoints |
|--------|---------|-----------|---|
| **KPI** | Production metrics (throughput, uptime) | `kpi_data` | `/api/v1/kpi/current`, `/history`, `/compare` |
| **Sales** | Sales transactions, trends, analysis | `sales_data`, `products` | `/api/v1/sales/summary`, `/trends`, `/top-products` |
| **Orders** | Order tracking and fulfillment | `orders_data` | `/api/v1/orders/status-summary`, `/list`, `/{id}` |
| **Quality** | Quality control metrics, defects | `quality_data` | `/api/v1/quality/summary`, `/defect-trends`, `/lots` |
| **Inventory** | Stock levels by location/warehouse | `inventory_data`, `products` | `/api/v1/inventory/levels` |
| **Sensors** | IoT sensor readings (temperature, pressure) | `sensor_data` | `/api/v1/sensors/readings` |
| **Output** | Production output tracking (units, lots) | `output_data` | `/api/v1/outputs` |

### Domain Pattern (Repeated for Each Domain)

Each domain has **4 core files:**

1. **Model** (`app/models/{domain}.py`) — SQLAlchemy ORM class
2. **Schema** (`app/schemas/{domain}.py`) — Pydantic request/response
3. **Service** (`app/services/{domain}_service.py`) — Business logic + sync method
4. **Router** (`app/routers/{domain}_router.py`) — FastAPI endpoints

**Example: KPI Domain**

```python
# app/models/kpi.py
class KPIData(Base):
    __tablename__ = "kpi_data"
    id: int = Column(Integer, primary_key=True)
    production_line: str = Column(String(50), nullable=False)
    throughput: float = Column(Float, nullable=False)
    uptime_percent: float = Column(Float, nullable=False)
    recorded_at: datetime = Column(DateTime(timezone=True), server_default=func.now())

# app/schemas/kpi.py
class KPICurrentResponse(BaseModel):
    id: int
    production_line: str
    throughput: float = Field(..., description="Units per hour")
    uptime_percent: float
    recorded_at: datetime
    class Config:
        from_attributes = True

# app/services/kpi_service.py
class KPIService:
    async def get_current_kpi(self, session: AsyncSession) -> list[KPIData]:
        result = await session.execute(select(KPIData).order_by(...).limit(1))
        return result.scalars().all()
    
    async def sync_kpi_from_gateway(self, session: AsyncSession) -> None:
        gateway_data = await gateway_client.get("/kpi/readings")
        for item in gateway_data:
            # Upsert logic: insert if new, update if exists
        await session.commit()

# app/routers/kpi_router.py
router = APIRouter(prefix="/api/v1/kpi", tags=["kpi"])
@router.get("/current", response_model=list[KPICurrentResponse])
async def get_current_kpi(session: AsyncSession = Depends(get_db)):
    return await kpi_service.get_current_kpi(session)
```

---

## Data Flow

### Synchronization Flow (Hourly)

```
External EFKO Gateway (HTTP API)
        ↓ (hourly via APScheduler)
APScheduler fires sync_all_data()
        ↓
For each domain:
  - Service calls: await gateway_client.get("/endpoint")
  - Parse JSON response
  - Upsert each record (insert if new, update if exists)
  - Commit to PostgreSQL
        ↓
PostgreSQL (local replica of remote data)
```

**Why hourly, not real-time?**
- Simplicity: No webhooks, no event bus
- Reliability: Sync is idempotent (safe to retry)
- Cost: Fewer external API calls
- Trade-off: Data is eventually consistent within 60 minutes

### Query Flow (On HTTP Request)

```
Client: GET /api/v1/kpi/current?date_from=2026-05-01&to=2026-05-07
    ↓
FastAPI receives request
    ↓
Pydantic validates query params (DateRangeParams schema)
    ↓
Route calls: await service.get_current_kpi(session, date_from, to)
    ↓
Service executes: SELECT * FROM kpi_data WHERE recorded_at BETWEEN ... AND ...
    ↓
ORM maps rows to KPIData model instances
    ↓
Service returns list[KPIData]
    ↓
Route returns: Pydantic serializes ORM models to JSON (from_attributes=True)
    ↓
Client receives: JSON array with typed fields
```

### JOIN Enrichment (Avoid N+1)

**✅ Good — One query with JOIN:**
```python
result = await session.execute(
    select(SalesData.id, SalesData.amount, Product.name.label("product_name"))
    .join(Product, SalesData.product_id == Product.id)
)
return [row._mapping for row in result.all()]
```

**❌ Bad — N+1 loop:**
```python
sales = await fetch_all_sales()  # Query 1
for sale in sales:
    product = await fetch_product(sale.product_id)  # Queries 2-N
```

---

## File Organization

```
DiplomaAPI/
├── app/
│   ├── main.py                          # FastAPI entry point, lifespan, middleware
│   ├── config.py                        # Settings from .env (DATABASE_URL, GATEWAY_URL, etc.)
│   ├── database.py                      # SQLAlchemy async engine + session factory
│   │
│   ├── models/                          # ORM models (SQLAlchemy)
│   │   ├── kpi.py                       # class KPIData(Base)
│   │   ├── sales.py                     # class SalesData(Base)
│   │   ├── orders.py
│   │   ├── quality.py
│   │   ├── inventory.py
│   │   ├── sensor.py
│   │   ├── output.py
│   │   └── product.py                   # Shared reference table
│   │
│   ├── schemas/                         # Pydantic request/response
│   │   ├── common.py                    # DateRangeParams, ErrorResponse
│   │   ├── kpi.py
│   │   ├── sales.py
│   │   ├── orders.py
│   │   ├── quality.py
│   │   ├── inventory.py
│   │   ├── sensors.py
│   │   ├── output.py
│   │   └── products.py
│   │
│   ├── services/                        # Business logic
│   │   ├── gateway_client.py            # httpx.AsyncClient for external API
│   │   ├── kpi_service.py               # class KPIService with sync & query methods
│   │   ├── sales_service.py
│   │   ├── order_service.py
│   │   ├── quality_service.py
│   │   ├── inventory_service.py
│   │   ├── sensor_service.py
│   │   ├── output_service.py
│   │   └── product_service.py
│   │
│   ├── routers/                         # FastAPI endpoints
│   │   ├── __init__.py                  # Exports all routers
│   │   ├── kpi_router.py                # @router.get/post endpoints
│   │   ├── sales_router.py
│   │   ├── orders_router.py
│   │   ├── quality_router.py
│   │   ├── inventory_router.py
│   │   ├── sensors_router.py
│   │   └── output_router.py
│   │
│   └── cron/
│       └── scheduler.py                 # APScheduler: hourly sync jobs
│
├── tests/
│   ├── conftest.py                      # pytest fixtures (testcontainers, session, client)
│   ├── unit/                            # Service unit tests
│   │   └── test_*_service.py
│   └── integration/                     # Route integration tests
│       └── test_*_routes.py
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                        # Versioned migrations (immutable)
│       ├── 001_add_kpi_table.py
│       ├── 002_add_sales_table.py
│       └── ...
│
├── docs/
│   ├── architecture.md                  # Three-layer design, constraints
│   ├── architecture-patterns.md         # 7 implementation patterns with code
│   ├── llm-api-gateway.md               # External Gateway API reference
│   └── README.md
│
├── .env                                 # Config (DATABASE_URL, GATEWAY_URL, GATEWAY_TOKEN)
├── .env.test                            # Test database URL
├── requirements.txt                     # Dependencies
├── docker-compose.yml                   # Local PostgreSQL
├── Dockerfile                           # App container
├── init.sh                              # Setup script
├── CLAUDE.md                            # Architecture overview + working rules
├── AGENTS.md                            # Startup checklist + definitions of done
├── feature_list.json                    # Feature tracking (status, evidence)
├── progress.md                          # Session logs + context
└── project.md                           # This file
```

---

## Working Rules (Mandatory)

1. **One feature at a time** — Complete it fully; update feature_list.json as you go
2. **Schema-first** — Define Pydantic schema → implement service → add route → write tests
3. **Business logic in services** — Routes never query DB directly; always delegate to service
4. **Type hints required** — All function arguments and returns must be typed; `mypy` must pass
5. **Async everywhere** — All I/O must be `async def` + `await`; no blocking calls
6. **Structured logging only** — Use `structlog.get_logger()`, never `print()`; logs are JSON
7. **Test services, not routes** — Service methods must have unit tests; route tests are redundant
8. **JOINs, not loops** — One query with JOIN; never N+1 loops
9. **Immutable migrations** — Never edit or delete migrations; always create new ones
10. **No hardcoded secrets** — All config from `.env`; never commit credentials
11. **Cron hourly** — Sync via APScheduler every 60 minutes; idempotent
12. **Specific errors** — Catch exceptions; return meaningful HTTP codes (200, 404, 500, etc.)

---

## Tech Stack Rationale

| Component | Technology | Why | Location |
|-----------|-----------|-----|----------|
| **Web Framework** | FastAPI 0.104+ | Async, fast, auto-docs (OpenAPI) | `app/main.py` |
| **ORM** | SQLAlchemy 2.x (async) | Type-safe, composable queries, async support | `app/database.py` |
| **Database** | PostgreSQL 14+ | ACID, rich types, reliability, production-proven | `.env` → `DATABASE_URL` |
| **HTTP Client** | httpx (async) | Async, connection pooling, timeouts | `app/services/gateway_client.py` |
| **Validation** | Pydantic v2 | Type validation, serialization, auto-docs | `app/schemas/` |
| **Migrations** | Alembic 1.12+ | Reversible, tracked schema changes | `alembic/versions/` |
| **Logging** | structlog (JSON) | Structured output, queryable in ELK/DataDog | `app/config.py` |
| **Scheduling** | APScheduler 3.x | Background cron jobs, hourly syncs | `app/cron/scheduler.py` |
| **Testing** | pytest + testcontainers | Real PostgreSQL in tests, async fixtures | `tests/` |
| **Type Checking** | mypy | Catch bugs before runtime | CLI: `mypy app/` |

---

## Key Constraints

### 1. PostgreSQL is the Source of Truth
- No in-memory caches without explicit invalidation
- All queries go through SQLAlchemy ORM
- No raw SQL execution (except migrations)

### 2. Gateway API is External
- Never query Gateway database directly
- All Gateway data comes through HTTP API calls
- Calls made by services via `gateway_client.py`
- Sync runs hourly; real-time sync not supported

### 3. Hourly Synchronization
```
APScheduler (every 60 min) → sync_all_data()
  → kpi_service.sync_kpi_from_gateway(session)
  → sales_service.sync_sales_from_gateway(session)
  → ... (all domains)
  → session.commit()
```
If a sync fails, error is logged; scheduler continues.

### 4. Immutable Migrations
```bash
# ✅ Do this: Create new migration
alembic revision -m "add sensor_data table"

# ❌ Never do this: Edit migration
# ❌ Never do this: Delete migration
```

### 5. Type Hints Required
All function signatures and return types must be typed:
```python
async def get_kpi_history(
    self,
    session: AsyncSession,
    date_from: datetime,
    to: datetime
) -> list[KPIData]:
    ...
```

### 6. Async Everywhere
```python
# ✅ All I/O async
result = await session.execute(select(...))
data = await gateway_client.get("/endpoint")

# ❌ Never blocking
import requests  # BAD
time.sleep(1)    # BAD
```

### 7. Structured Logging
```python
import structlog
logger = structlog.get_logger()

# ✅ Structured logs (JSON)
logger.info("kpi_fetched", count=len(results), line_id=line)

# ❌ Never unstructured
print(f"Fetched {len(results)} records")
```

---

## Implementation Patterns

### Pattern 1: New Endpoint

1. Define schema (request/response)
2. Write service method (business logic)
3. Add thin route (delegates to service)
4. Write unit test for service

```python
# 1. Schema
class KPICurrentResponse(BaseModel):
    id: int; production_line: str; throughput: float
    class Config:
        from_attributes = True

# 2. Service
class KPIService:
    async def get_current_kpi(self, session: AsyncSession) -> list[KPIData]:
        return await session.execute(select(KPIData).order_by(...).limit(1)).scalars().all()

# 3. Route
@router.get("/current", response_model=list[KPICurrentResponse])
async def get_current_kpi(session: AsyncSession = Depends(get_db)):
    return await kpi_service.get_current_kpi(session)

# 4. Test
@pytest.mark.asyncio
async def test_get_current_kpi(session):
    session.add(KPIData(...))
    await session.commit()
    result = await service.get_current_kpi(session)
    assert len(result) == 1
```

### Pattern 2: New Table

1. Create ORM model
2. Create Alembic migration
3. Implement service methods (query + sync)
4. Add routes

```python
# 1. Model
class SensorData(Base):
    __tablename__ = "sensor_data"
    id: int = Column(Integer, primary_key=True)
    sensor_id: str = Column(String(50), unique=True)
    temperature: float = Column(Float, nullable=True)
    recorded_at: datetime = Column(DateTime(timezone=True), server_default=func.now())

# 2. Migration
alembic revision -m "add sensor_data table"
# Edit alembic/versions/xxx.py with op.create_table(...)

# 3. Service
class SensorService:
    async def get_sensor_readings(self, session: AsyncSession) -> list[SensorData]:
        return await session.execute(select(SensorData).order_by(...)).scalars().all()
    
    async def sync_sensor_readings_from_gateway(self, session: AsyncSession) -> None:
        data = await gateway_client.get("/sensors/readings")
        for item in data:
            existing = await session.execute(select(SensorData).where(...))
            if existing.scalar_one_or_none():
                # Update
            else:
                session.add(SensorData(...))
        await session.commit()

# 4. Routes
@router.get("/readings", response_model=list[SensorReadingResponse])
async def get_sensor_readings(session: AsyncSession = Depends(get_db)):
    return await sensor_service.get_sensor_readings(session)
```

### Pattern 3: Sync from Gateway

```python
async def sync_sales_from_gateway(self, session: AsyncSession) -> None:
    try:
        # 1. Fetch from Gateway
        gateway_data = await gateway_client.get("/sales/latest")
        logger.info("gateway_fetch_success", endpoint="/sales/latest", count=len(gateway_data))
        
        # 2. Upsert: insert if new, update if exists
        for item in gateway_data:
            existing = await session.execute(
                select(SalesData).where(SalesData.source_id == item["id"])
            )
            sale = existing.scalar_one_or_none()
            
            if sale:
                sale.amount = item["amount"]
                sale.region = item["region"]
            else:
                session.add(SalesData(source_id=item["id"], amount=item["amount"], ...))
        
        # 3. Commit all
        await session.commit()
        logger.info("sales_sync_completed", count=len(gateway_data))
        
    except Exception as e:
        logger.error("sales_sync_failed", error=str(e))
        # Don't re-raise; let scheduler continue
```

### Pattern 4: JOIN Enrichment (No N+1)

```python
# Bad: N+1
sales = await fetch_all_sales()
for sale in sales:
    product = await fetch_product(sale.product_id)  # Loop × N queries

# Good: One query with JOIN
result = await session.execute(
    select(
        SalesData.id,
        SalesData.amount,
        Product.name.label("product_name")
    )
    .join(Product, SalesData.product_id == Product.id)
    .order_by(SalesData.recorded_at.desc())
)
return [row._mapping for row in result.all()]
```

### Pattern 5: Date Filtering

```python
# Schema
class DateRangeParams(BaseModel):
    date_from: datetime = Field(
        default_factory=lambda: datetime.now() - timedelta(days=30),
        alias="date_from"
    )
    to: datetime = Field(default_factory=datetime.now, alias="to")
    class Config:
        populate_by_name = True

# Route
@router.get("/history", response_model=list[KPIHistoryResponse])
async def get_kpi_history(
    params: DateRangeParams = Depends(),
    session: AsyncSession = Depends(get_db)
):
    return await kpi_service.get_kpi_history(session, params.date_from, params.to)

# Service
async def get_kpi_history(self, session, date_from, to):
    return await session.execute(
        select(KPIData)
        .where((KPIData.recorded_at >= date_from) & (KPIData.recorded_at <= to))
        .order_by(KPIData.recorded_at.desc())
    ).scalars().all()
```

### Pattern 6: Testing with Testcontainers

```python
# conftest.py
@pytest.fixture(scope="session")
def postgres_db():
    container = PostgresContainer("postgres:14")
    container.start()
    yield container
    container.stop()

@pytest.fixture
async def session(postgres_db):
    engine = create_async_engine(postgres_db.get_connection_url())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession)
    async with SessionLocal() as db_session:
        yield db_session

# Unit test (service)
@pytest.mark.asyncio
async def test_get_top_products(session):
    session.add(SalesData(product_id=1, amount=100))
    session.add(SalesData(product_id=1, amount=50))
    await session.commit()
    
    result = await sales_service.get_top_products(session, limit=1)
    assert len(result) == 1
    assert result[0].total_amount == 150
```

### Pattern 7: Error Handling

```python
@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(order_id: int, session: AsyncSession = Depends(get_db)):
    try:
        result = await session.execute(select(OrderData).where(OrderData.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            logger.warning("order_not_found", order_id=order_id)
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        logger.info("order_retrieved", order_id=order_id)
        return order
        
    except SQLAlchemyError as e:
        logger.error("database_error", order_id=order_id, error=str(e))
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error("unexpected_error", order_id=order_id, error=str(e))
        raise HTTPException(status_code=500, detail="Unexpected error")
```

---

## Development Workflow

### Start of Session
1. Read `CLAUDE.md` (architecture overview)
2. Read `AGENTS.md` (working rules)
3. Check `feature_list.json` (what's in progress)
4. Run `./init.sh` (verify environment)
5. Read `progress.md` (context from prior sessions)

### During Work
1. Pick one feature from `feature_list.json`
2. Follow pattern: Schema → Service → Route → Tests
3. Run `pytest tests/ -v` frequently
4. Use `mypy app/` to catch type errors
5. Use `ruff check app/` to lint

### End of Session
1. `pytest tests/ -v` — all tests pass
2. `mypy app/ --ignore-missing-imports` — no type errors
3. Update `feature_list.json` with completion status
4. Update `progress.md` with context for next session
5. Commit: `git commit -m "feat: description and why"`
6. Verify: `git log --oneline -5`

---

## Common Commands

```bash
# Testing
pytest tests/ -v                          # Run all tests
pytest tests/unit/ -v                     # Unit tests only
pytest tests/integration/ -v              # Integration tests only

# Type checking
mypy app/ --ignore-missing-imports        # Check types

# Linting
ruff check app/                           # Find style issues
ruff format app/                          # Auto-fix style

# Running
uvicorn app.main:app --reload             # Dev server (http://localhost:8000/docs)

# Database migrations
alembic revision -m "add table"           # Create new migration
alembic upgrade head                      # Apply migrations
alembic downgrade -1                      # Rollback one migration

# Git
git log --oneline -10                     # Recent commits
git status                                # Working tree status
git diff app/services/                    # Changes in services/
```

---

## Key Gotchas

### UUID ↔ varchar JOINs

If `product_id` is UUID and `Product.source_system_id` is varchar, **cast to String:**

```python
from sqlalchemy import cast, String

# ❌ Fails: "operator does not exist: uuid = character varying"
select(SalesData, Product.name).join(
    Product,
    SalesData.product_id == Product.source_system_id
)

# ✅ Works: Cast UUID to String
select(SalesData, Product.name).join(
    Product,
    cast(SalesData.product_id, String) == Product.source_system_id
)
```

### Date Filtering Query Parameter

Use `date_from`, **not** `from` (reserved Python keyword):

```python
# ❌ Can't use 'from' — Python keyword
GET /api/v1/kpi/history?from=2026-05-01&to=2026-05-07

# ✅ Use 'date_from'
GET /api/v1/kpi/history?date_from=2026-05-01&to=2026-05-07
```

### Testcontainers PostgreSQL Requires Docker

Tests use real PostgreSQL in containers:

```bash
# Start Docker
docker daemon

# Then run tests
pytest tests/ -v
```

Alternatively, use `.env.test` with local PostgreSQL:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/diploma_test
pytest tests/ -v
```

### Never Edit Migrations

✅ **Correct:**
```bash
alembic revision -m "fix: add missing index"
# Edit new file alembic/versions/xxx.py
```

❌ **Wrong:**
```bash
# DO NOT edit or delete alembic/versions/001_add_kpi_table.py
```

---

## Extending the Project

### To Add a New Domain

1. Create `app/models/{domain}.py` with SQLAlchemy ORM class
2. Create `app/schemas/{domain}.py` with Pydantic request/response schemas
3. Create `app/services/{domain}_service.py` with:
   - Query methods (e.g., `get_{domain}`)
   - Sync method: `sync_{domain}_from_gateway()`
4. Create `app/routers/{domain}_router.py` with FastAPI endpoints
5. Create migration: `alembic revision -m "add {domain} table"`
6. Create tests: `tests/unit/test_{domain}_service.py`
7. Register router in `app/main.py` or `app/routers/__init__.py`
8. Update `feature_list.json` to track progress

### To Add a New Endpoint to Existing Domain

1. Add Pydantic response schema to `app/schemas/{domain}.py`
2. Add service method to `app/services/{domain}_service.py`
3. Add `@router.get/post` to `app/routers/{domain}_router.py`
4. Add unit test to `tests/unit/test_{domain}_service.py`
5. Optional: Add integration test to `tests/integration/test_{domain}_routes.py`

---

## Performance Considerations

### N+1 Queries
Use JOIN instead of loops:
```python
# Bad: N queries
for sale in await fetch_all_sales():
    product = await fetch_product(sale.product_id)

# Good: 1 query
select(...).join(Product, ...)
```

### Pagination
Use `limit` and `offset` for large result sets:
```python
select(SalesData).limit(20).offset(0)  # First page
select(SalesData).limit(20).offset(20) # Second page
```

### Indices
Add indices to frequently-filtered columns:
```python
class SalesData(Base):
    __tablename__ = "sales_data"
    recorded_at = Column(DateTime, index=True)  # For date filtering
    product_id = Column(UUID, index=True)       # For JOINs
```

### Connection Pooling
SQLAlchemy async engine automatically pools connections. No tuning needed for development.

---

## Security & Secrets

### Config from Environment
All secrets from `.env`:
```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/diploma_api
GATEWAY_URL=https://gateway.example.com
GATEWAY_TOKEN=sk_live_secret_token_here
```

Loaded in `app/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    gateway_url: str
    gateway_token: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Never Hardcode Secrets
```python
# ❌ Wrong
GATEWAY_TOKEN = "sk_live_secret"

# ✅ Right
GATEWAY_TOKEN = os.getenv("GATEWAY_TOKEN")
```

---

## Logging & Debugging

### Structured Logging
All logs are JSON (searchable, indexed):
```python
import structlog
logger = structlog.get_logger()

logger.info("sales_sync_completed", count=150, duration_seconds=12.5)
# Output: {"event": "sales_sync_completed", "count": 150, "duration_seconds": 12.5}
```

### Enable SQL Logging (Development Only)
```python
engine = create_async_engine(DATABASE_URL, echo=True)  # Print all SQL
```

### Print Request/Response (Development Only)
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(...)  # See app/main.py for full setup
```

---

## Monitoring & Observability

### APScheduler Job Logs
Each hourly sync is logged:
```python
logger.info("sync_all_data_started")
# ... per-domain syncs ...
logger.info("all_syncs_completed")
```

### Metrics
Track sync duration, error rates, records processed:
```python
start = time.time()
await kpi_service.sync_kpi_from_gateway(session)
duration = time.time() - start
logger.info("kpi_sync_completed", duration=duration, records=count)
```

---

## Deployment

### Docker Build
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ app/
COPY alembic/ alembic/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables (Production)
```bash
DATABASE_URL=postgresql+asyncpg://prod_user:strong_password@db.example.com/diploma_prod
GATEWAY_URL=https://gateway.example.com
GATEWAY_TOKEN=sk_live_secret
LOG_LEVEL=INFO
```

### Database Migrations (Before Deploy)
```bash
alembic upgrade head  # Apply all pending migrations
```

---

## Summary

DiplomaAPI is a **three-layer async FastAPI service** that aggregates production data from external microservices, syncs hourly via cron, and exposes analytical endpoints. Built for scalability, testability, and maintainability with:

- **Separation of concerns:** Routes delegate to services; services query the database
- **Type safety:** Full type hints; Pydantic for validation
- **Async throughout:** Non-blocking I/O for high concurrency
- **Immutable migrations:** Reversible schema versioning
- **Structured logging:** JSON logs for observability
- **Testability:** Real PostgreSQL in tests via testcontainers
- **Domain-driven design:** 7 independent domains (KPI, Sales, Orders, Quality, Inventory, Sensors, Output)

To add a feature, follow the **schema → service → route → tests** pattern. To deploy, apply migrations and start the container. To understand a bug, check the service layer (where the logic lives) and the logs (structured JSON).
