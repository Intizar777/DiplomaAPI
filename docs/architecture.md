# Architecture

DiplomaAPI follows a **three-layer, async-first architecture** designed for scalability, testability, and maintainability.

---

## Three-Layer Design

```
┌─────────────────────────────────────────────┐
│  Route Layer (Thin Validation)              │
│  - FastAPI endpoints                        │
│  - Validate input with Pydantic schemas     │
│  - Delegate to services                     │
└──────────────┬──────────────────────────────┘
               │ depends_on
┌──────────────▼──────────────────────────────┐
│  Service Layer (Business Logic)             │
│  - All application logic lives here         │
│  - Database queries with SQLAlchemy         │
│  - Gateway API calls via httpx              │
│  - Structured logging with structlog        │
└──────────────┬──────────────────────────────┘
               │ uses
┌──────────────▼──────────────────────────────┐
│  Database Layer (ORM + Schema)              │
│  - SQLAlchemy 2.x async models              │
│  - PostgreSQL 14+ persistent storage        │
│  - Alembic migrations (immutable)           │
└─────────────────────────────────────────────┘
```

### Route Layer

**Purpose:** Validate input, authorize (if needed), delegate to service.

**Characteristics:**
- Thin: 3-5 lines per endpoint
- Uses Pydantic schemas for request/response validation
- Never queries database directly
- Never contains business logic
- Just `await service.method()` and return

**Example:**
```python
@router.get("/current", response_model=list[KPICurrentResponse])
async def get_current_kpi(
    session: AsyncSession = Depends(get_db)
) -> list[KPICurrentResponse]:
    """Get current KPI metrics."""
    return await kpi_service.get_current_kpi(session)
```

### Service Layer

**Purpose:** Implement all business logic, query database, call Gateway API.

**Characteristics:**
- Contains all domain logic
- Queries database with SQLAlchemy ORM
- Calls Gateway API via `gateway_client`
- Logs with `structlog`
- Uses `async def` and `await` for all I/O
- Testable in isolation (no HTTP/FastAPI dependencies)

**Example:**
```python
class KPIService:
    async def get_current_kpi(self, session: AsyncSession) -> list[KPIData]:
        """Fetch latest KPI reading for each production line."""
        result = await session.execute(
            select(KPIData)
            .order_by(KPIData.recorded_at.desc())
            .limit(1)
        )
        kpi_list = result.scalars().all()
        logger.info("kpi_fetched", count=len(kpi_list))
        return kpi_list
```

### Database Layer

**Purpose:** Define data schema, manage persistence, provide async access.

**Characteristics:**
- SQLAlchemy ORM models (not raw SQL)
- Async engine and session factory
- Alembic migrations (versioned, immutable)
- PostgreSQL types and constraints

**Example:**
```python
class KPIData(Base):
    __tablename__ = "kpi_data"
    
    id: int = Column(Integer, primary_key=True)
    production_line: str = Column(String(50), nullable=False)
    throughput: float = Column(Float, nullable=False)
    uptime_percent: float = Column(Float, nullable=False)
    recorded_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
```

---

## Why This Architecture Works

| Benefit | How We Achieve It |
|---------|-------------------|
| **Testable** | Services have no HTTP/FastAPI dependencies; test with just a database session |
| **Reusable** | Services can be called from routes, cron jobs, or other services |
| **Maintainable** | Logic is localized; know where to look for bugs |
| **Async throughout** | All I/O is non-blocking; maximum throughput |
| **Scalable** | No N+1 queries; JOINs enrich data in one round-trip |
| **Auditable** | Structured logging captures all operations |

---

## Domain Architecture

DiplomaAPI aggregates data from **7 domains**, each with its own:
- **Model** — SQLAlchemy ORM class (app/models/{domain}.py)
- **Schema** — Pydantic request/response (app/schemas/{domain}.py)
- **Service** — Business logic and Gateway sync (app/services/{domain}_service.py)
- **Router** — FastAPI endpoints (app/routers/{domain}_router.py)
- **Tests** — Unit + integration tests (tests/unit + tests/integration)

### Domains

| Domain | Purpose | Key Tables | Key Endpoints |
|--------|---------|-----------|----------------|
| **KPI** | Production metrics (throughput, uptime) | `kpi_data` | `/api/v1/kpi/current`, `/history`, `/compare` |
| **Sales** | Sales transactions, trends, analysis | `sales_data`, `products` | `/api/v1/sales/summary`, `/trends`, `/top-products` |
| **Orders** | Order tracking and status | `orders_data` | `/api/v1/orders/status-summary`, `/list`, `/{id}` |
| **Quality** | Quality metrics, defect tracking | `quality_data` | `/api/v1/quality/summary`, `/defect-trends`, `/lots` |
| **Inventory** | Stock levels by location | `inventory_data`, `products` | `/api/v1/inventory/levels` |
| **Sensors** | IoT sensor readings (temperature, pressure) | `sensor_data` | `/api/v1/sensors/readings` |
| **Output** | Production output tracking | `output_data` | `/api/v1/outputs` |

### Common Pattern Across All Domains

Every domain has a **sync method** called hourly by APScheduler:

```python
async def sync_{domain}_from_gateway(self, session: AsyncSession) -> None:
    """Fetch latest data from Gateway API and upsert into database."""
    gateway_data = await gateway_client.get("/endpoint")
    for item in gateway_data:
        # Check if exists
        existing = await session.execute(...)
        if existing:
            # Update
        else:
            # Insert
    await session.commit()
```

This keeps the local PostgreSQL data lake synchronized with the external EFKO Gateway.

---

## Key Architectural Constraints

### 1. PostgreSQL is the Source of Truth

- No in-memory caches without explicit invalidation
- All queries go through SQLAlchemy ORM
- No direct SQL execution (except migrations)

### 2. Gateway API is External

- Never query Gateway database directly
- All Gateway data comes through HTTP API calls
- Calls are made by services via `gateway_client.py`
- Sync runs hourly; real-time sync not supported

### 3. Hourly Synchronization

```
Gateway API (external) ──HTTP──> APScheduler (cron) ──> Services ──> PostgreSQL
         ↑                                                                 ↓
         └─────────────── Sync runs every 60 minutes ────────────────────┘
```

- APScheduler runs `sync_all_data()` every 60 minutes
- Each service's `sync_*_from_gateway()` method is called
- If a sync fails, error is logged; scheduler continues
- No real-time sync; data is eventually consistent (within 60 min)

### 4. Immutable Migrations

- Alembic migrations are **never edited or deleted**
- Always create a new migration for schema changes
- Migrations are the source of truth for database schema
- Rollback is done with `alembic downgrade -1`

### 5. Type Hints Required

- All function arguments and return types must have types
- `mypy` must pass (enables static type checking)
- Catches bugs at development time, not runtime

### 6. Async Everywhere

- All I/O operations must be `async def` + `await`
- No blocking calls (no synchronous libraries)
- Enables high concurrency and throughput

### 7. Structured Logging Only

- Use `structlog.get_logger()` throughout
- Log operations as JSON (searchable and indexable)
- Never use `print()` statements

### 8. Schema-First Design

- Pydantic schemas define the API contract
- Schemas are validated on all requests
- Enable automatic OpenAPI documentation

---

## Tech Stack

| Layer | Component | Technology | Why |
|-------|-----------|-----------|-----|
| **Framework** | HTTP | FastAPI 0.104+ | Async, fast, auto-docs (OpenAPI) |
| **ORM** | Database Access | SQLAlchemy 2.x (async) | Type-safe, composable queries, async support |
| **Database** | Storage | PostgreSQL 14+ | ACID transactions, rich types, reliability |
| **HTTP Client** | Gateway Calls | httpx (async) | Async HTTP client, connection pooling |
| **Validation** | Input/Output | Pydantic v2 | Type validation, serialization, documentation |
| **Migrations** | Schema Versioning | Alembic 1.12+ | Reversible, tracked schema changes |
| **Logging** | Observability | structlog (JSON) | Structured logging, queryable JSON output |
| **Scheduling** | Cron Jobs | APScheduler 3.x | Background tasks, hourly sync jobs |
| **Testing** | Verification | pytest + testcontainers | Real PostgreSQL in tests, async fixtures |
| **Type Checking** | Static Analysis | mypy | Catch bugs before runtime |

---

## Data Flow

### Synchronization Flow (Hourly)

```
1. APScheduler fires "sync_all_data" job
2. For each service (KPI, Sales, Orders, Quality, Inventory, Sensors, Output):
   a. Service calls: await gateway_client.get("/endpoint")
   b. Parse response JSON
   c. Upsert each record (insert if new, update if exists)
   d. Commit to PostgreSQL
3. Log completion: logger.info("all_syncs_completed")
4. Wait 60 minutes, repeat
```

### Query Flow (On HTTP Request)

```
1. HTTP GET /api/v1/kpi/current?date_from=...&to=...
2. FastAPI receives request
3. Pydantic validates query params (DateRangeParams schema)
4. Route calls: await service.get_current_kpi(session)
5. Service executes: SELECT * FROM kpi_data WHERE recorded_at BETWEEN ...
6. ORM maps rows to KPIData model
7. Service returns list[KPIData]
8. Route returns JSON via Pydantic response_model
9. Client receives JSON response
```

### Enrichment Flow (JOIN Example)

```
1. Service needs product_name alongside sales data
2. Service executes: SELECT sales.*, products.name 
                     FROM sales_data 
                     JOIN products ON sales.product_id = products.id
3. One database round-trip, all data together
4. Service returns list[SalesWithProduct]
5. Route returns JSON

(NOT: fetch 100 sales, then loop 100× to fetch product names — that's N+1)
```

---

## Project File Organization

```
DiplomaAPI/
├── app/
│   ├── main.py              # FastAPI entry, lifespan, middleware
│   ├── config.py            # Settings from .env
│   ├── database.py          # SQLAlchemy async engine + session factory
│   │
│   ├── models/              # ORM models (one per domain)
│   │   ├── kpi.py
│   │   ├── sales.py
│   │   ├── orders.py
│   │   ├── quality.py
│   │   ├── inventory.py
│   │   ├── sensor.py
│   │   ├── output.py
│   │   └── product.py       # Reference table (shared across domains)
│   │
│   ├── schemas/             # Pydantic request/response schemas (one per domain)
│   │   ├── common.py        # Shared: DateRangeParams, ErrorResponse
│   │   ├── kpi.py
│   │   ├── sales.py
│   │   ├── orders.py
│   │   ├── quality.py
│   │   ├── inventory.py
│   │   ├── sensors.py
│   │   ├── output.py
│   │   └── products.py
│   │
│   ├── services/            # Business logic (one per domain)
│   │   ├── gateway_client.py    # httpx AsyncClient for external API
│   │   ├── kpi_service.py
│   │   ├── sales_service.py
│   │   ├── order_service.py
│   │   ├── quality_service.py
│   │   ├── inventory_service.py
│   │   ├── sensor_service.py
│   │   ├── output_service.py
│   │   └── product_service.py
│   │
│   ├── routers/             # FastAPI endpoints (one per domain)
│   │   ├── __init__.py      # Exports all routers
│   │   ├── kpi_router.py
│   │   ├── sales_router.py
│   │   ├── orders_router.py
│   │   ├── quality_router.py
│   │   ├── inventory_router.py
│   │   ├── sensors_router.py
│   │   ├── output_router.py
│   │   └── products_router.py
│   │
│   └── cron/
│       └── scheduler.py     # APScheduler: hourly sync jobs
│
├── tests/
│   ├── conftest.py          # pytest fixtures (testcontainers, session, client)
│   ├── unit/                # Service unit tests
│   │   ├── test_kpi_service.py
│   │   ├── test_sales_service.py
│   │   └── ...
│   └── integration/         # Route integration tests
│       ├── test_kpi_routes.py
│       ├── test_sales_routes.py
│       └── ...
│
├── alembic/                 # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/            # Versioned migration files
│
├── docs/                    # Documentation
│   ├── architecture.md      # This file
│   ├── architecture-patterns.md
│   └── README.md
│
├── .env                     # Config (DATABASE_URL, GATEWAY_URL, GATEWAY_TOKEN)
├── requirements.txt         # Dependencies
├── docker-compose.yml       # Local PostgreSQL
├── Dockerfile               # App container
├── init.sh                  # Setup script
├── CLAUDE.md                # Architecture overview (this guide)
├── AGENTS.md                # Working rules & startup
├── feature_list.json        # Feature tracking
└── progress.md              # Session logs
```

---

## Design Decisions

### Why Three Layers?

- **Testability:** Test services without mocking FastAPI or HTTP
- **Reusability:** Same service can be called from route, cron, or CLI
- **Maintainability:** Logic is in one place (service), not scattered across routes
- **Clarity:** Know where to look for bugs (service has the logic, route just delegates)

### Why Pydantic Schemas for Everything?

- **Validation:** Input is validated before reaching service
- **Documentation:** Schemas auto-generate OpenAPI docs at `/docs`
- **Serialization:** ORM models are serialized to JSON via `from_attributes=True`
- **Type Safety:** Runtime validation catches bugs

### Why SQLAlchemy ORM, Not Raw SQL?

- **Composability:** Build queries step-by-step, reuse parts
- **Type Safety:** Column types are checked at build time
- **Portability:** Could switch databases if needed (though not recommended)
- **Testability:** Easier to mock or test with different connections

### Why Async Everywhere?

- **Throughput:** Non-blocking I/O handles thousands of concurrent requests
- **Simplicity:** No thread pools, no locking issues
- **Python 3.8+:** Native async/await language support

### Why Hourly Sync, Not Real-Time?

- **Simplicity:** No webhook handlers, no event bus complexity
- **Reliability:** Sync is idempotent (safe to retry)
- **Costs:** Fewer API calls to external Gateway
- **Trade-off:** Data is eventually consistent within 60 minutes

---

## Related Documentation

- **[docs/architecture-patterns.md](architecture-patterns.md)** — 7 detailed implementation patterns with code examples
- **[CLAUDE.md](../CLAUDE.md)** — Working rules, definition of done, quick reference
- **[AGENTS.md](../AGENTS.md)** — Startup checklist, verification commands
- **[feature_list.json](../feature_list.json)** — Feature status tracking

---

**Last updated:** 2026-05-07
