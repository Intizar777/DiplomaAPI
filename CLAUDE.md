# CLAUDE.md

Architecture, patterns, and technical decisions for the Dashboard Analytics API. Read this when making architectural decisions or extending the codebase.

---

## Project Overview

**Name:** Dashboard Analytics API  
**Purpose:** Aggregate and analyze production, sales, orders, quality, and inventory data from the EFKO microservices gateway  
**Tech Stack:** FastAPI, SQLAlchemy 2.x (async), PostgreSQL, Pydantic v2, APScheduler  
**Production:** Docker containerized, environment-driven configuration  

---

## Architecture

### Request Flow

```
Client HTTP Request
    ↓
[FastAPI Router] → validates input with Pydantic schema
    ↓
[Service Layer] → executes business logic, queries database
    ↓
[SQLAlchemy ORM] → async queries to PostgreSQL
    ↓
[Response] → serialized Pydantic schema to JSON
```

**Rule:** Routes are thin. All business logic lives in services.

### Data Synchronization Flow

```
[APScheduler: hourly tick]
    ↓
[app/cron/scheduler.py: start_scheduler()]
    ↓
[Service: sync_*_from_gateway()]
    ↓
[HTTPx: async call to GATEWAY_URL]
    ↓
[Service: parse & store in PostgreSQL]
    ↓
[Logging: structured log of success/failure]
```

**Rule:** Cron jobs use services, never raw database queries.

---

## Domain Architecture

Each domain (KPI, Sales, Orders, etc.) follows the same pattern:

```
Domain/
├── Router     (app/routers/{domain}_router.py)
│   ├─ GET /api/v1/{domain}/...
│   └─ Delegates all logic to Service
│
├── Schema     (app/schemas/{domain}.py)
│   ├─ Request schema: input validation
│   └─ Response schema: output serialization
│
├── Model      (app/models/{domain}.py)
│   ├─ SQLAlchemy ORM class
│   ├─ __tablename__ = "{domain}_data"
│   └─ Relationships to other tables (e.g., Product)
│
└── Service    (app/services/{domain}_service.py)
    ├─ Query methods (get_*, list_*)
    ├─ Aggregation logic (sum, avg, group_by)
    ├─ Sync methods (sync_from_gateway)
    └─ Transformation logic (enrich data, add product_name)
```

**Example: Adding "Top Products" endpoint**

```
1. Schema      → app/schemas/sales.py: TopProductsResponse
2. Service     → app/services/sales_service.py: async def get_top_products()
3. Router      → app/routers/sales_router.py: @router.get("/top-products")
4. Test        → tests/test_sales.py: async def test_get_top_products()
5. Verify      → pytest tests/ && mypy app/
```

---

## Database Design

### Key Principles

1. **Async SQLAlchemy** — All queries use `sessionmaker(bind=engine, class_=AsyncSession)`
2. **Normalized schema** — Reference tables (Products, Warehouses) join with data tables
3. **Timestamp tracking** — Each table has `created_at` and `updated_at` for auditing
4. **No cascading deletes** — Foreign keys use `ondelete="RESTRICT"` to prevent accidents
5. **Migrations are immutable** — Each migration is append-only; never modify or delete

### Core Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| **kpi_data** | Production metrics | `period`, `metric_name`, `value`, `source_system_id` |
| **sales_data** | Sales transactions | `date`, `amount`, `quantity`, `product_id`, `warehouse_id` |
| **orders_data** | Order records | `order_id`, `status`, `created_at`, `updated_at` |
| **quality_data** | Quality metrics | `lot_id`, `defect_count`, `inspection_date` |
| **inventory_data** | Stock levels | `warehouse_id`, `product_id`, `quantity`, `last_synced` |
| **products** | Product reference | `id`, `name`, `sku`, `source_system_id` |
| **warehouses** | Warehouse reference | `id`, `name`, `region` |

### Relationships

```python
# Sales data references Products and Warehouses
sales_data.product_id → products.id
sales_data.warehouse_id → warehouses.id

# Inventory data references Products and Warehouses
inventory_data.product_id → products.id
inventory_data.warehouse_id → warehouses.id

# KPI data references source systems (source_system_id is text, not FK)
kpi_data.source_system_id → external reference, no FK
```

### Critical Queries

**Join pattern for enriching data with product names:**

```python
# In services
query = select(
    SalesData.amount,
    SalesData.quantity,
    Product.name.label("product_name"),
    Warehouse.name.label("warehouse_name")
).join(
    Product, SalesData.product_id == Product.id  # ← Note: always use product_id
).join(
    Warehouse, SalesData.warehouse_id == Warehouse.id
)
result = await session.execute(query)
```

**Aggregation pattern:**

```python
# Count by product
query = select(
    Product.name,
    func.count(SalesData.id).label("total_sales")
).join(
    SalesData, Product.id == SalesData.product_id
).group_by(Product.id, Product.name)
```

---

## API Design

### Request/Response Pattern

**All requests use Pydantic schemas for validation:**

```python
# In schemas/sales.py
class SalesFilterRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    warehouse_id: int | None = None
    product_id: int | None = None

    model_config = ConfigDict(from_attributes=True)

# In routers/sales_router.py
@router.get("/summary", response_model=SalesSummaryResponse)
async def get_sales_summary(filter: SalesFilterRequest = Depends()) -> SalesSummaryResponse:
    result = await sales_service.get_summary(filter)
    return SalesSummaryResponse(**result)
```

### Status Code Convention

| Code | When to Use |
|------|------------|
| **200** | Successful GET, always return data (even if empty) |
| **201** | POST creates a resource |
| **400** | Invalid request (schema validation failed) |
| **404** | Resource not found (return empty list instead when listing) |
| **500** | Unhandled exception; log context before returning |

**Rule:** Never return 404 for list endpoints. Return 200 with empty list.

### Error Handling

**Always catch specific exceptions:**

```python
try:
    result = await service.get_data()
except ValueError as e:
    logger.error("validation_error", error=str(e))
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error("unexpected_error", error=str(e), exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Asynchronous Patterns

### Database Session Management

```python
# In database.py
async_session = sessionmaker(
    engine=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# In services
async with async_session() as session:
    result = await session.execute(query)
    data = result.scalars().all()
```

### HTTP Client Usage

```python
# In services/gateway_client.py
async with httpx.AsyncClient() as client:
    response = await client.get(
        url=f"{settings.GATEWAY_URL}/endpoint",
        headers={"Authorization": f"Bearer {settings.GATEWAY_TOKEN}"},
        timeout=30.0
    )
    return response.json()
```

### Background Tasks (Cron)

```python
# In cron/scheduler.py
scheduler = AsyncScheduler(daemon=False)

@scheduler.scheduled_job('interval', minutes=settings.SYNC_INTERVAL_MINUTES)
async def sync_all_data():
    logger.info("sync_started")
    try:
        await sales_service.sync_from_gateway()
        await kpi_service.sync_from_gateway()
        logger.info("sync_completed")
    except Exception as e:
        logger.error("sync_failed", error=str(e), exc_info=True)

# In main.py lifespan
async def lifespan(app: FastAPI):
    await start_scheduler()
    yield
    await stop_scheduler()
```

---

## Testing Strategy

### Unit Tests (Business Logic)

Test services in isolation:

```python
# tests/test_sales_service.py
@pytest.fixture
async def session():
    # In-memory SQLite or test database
    async with AsyncSession(test_engine) as s:
        yield s

@pytest.mark.asyncio
async def test_get_top_products(session):
    # Arrange: insert test data
    await session.add(Product(name="Widget", sku="W001"))
    await session.commit()
    
    # Act
    result = await sales_service.get_top_products(session)
    
    # Assert
    assert len(result) > 0
    assert result[0].name == "Widget"
```

### Integration Tests (Routes)

Test end-to-end with a test client:

```python
# tests/test_sales_routes.py
@pytest.mark.asyncio
async def test_sales_summary_endpoint(client):
    response = await client.get("/api/v1/sales/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_amount" in data
```

### When to Skip Tests

- ✅ Test service methods and business logic
- ✅ Test complex queries
- ❌ Skip testing routes that only delegate to tested services
- ❌ Skip testing ORM model definitions (SQLAlchemy handles that)

---

## Configuration & Environment

### Environment Variables

All config comes from `.env`. Never hardcode. Pattern:

```python
# In config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    GATEWAY_URL: str
    GATEWAY_TOKEN: str
    SYNC_INTERVAL_MINUTES: int = 60
    RETENTION_DAYS: int = 90
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

# In services
logger.info(f"Syncing from {settings.GATEWAY_URL}")
```

### Local Development Setup

```bash
# 1. Copy template
cp .env.example .env

# 2. Edit .env for your local database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dashboard_api

# 3. Run migrations
alembic upgrade head

# 4. Start app
uvicorn app.main:app --reload

# 5. Visit http://localhost:8000/docs
```

### Docker Production Setup

```bash
# Uses docker-compose.yml for postgres + app
docker-compose up --build

# Check health
curl http://localhost:8000/health
```

---

## Common Patterns & How to Apply Them

### Pattern 1: Adding a New Endpoint

**Example: GET /api/v1/sales/revenue-by-region**

```python
# 1. Schema (app/schemas/sales.py)
class RevenueByRegionResponse(BaseModel):
    region: str
    total_revenue: float
    order_count: int

# 2. Service (app/services/sales_service.py)
async def get_revenue_by_region(self, session: AsyncSession) -> list[dict]:
    query = select(
        Warehouse.region,
        func.sum(SalesData.amount).label("total_revenue"),
        func.count(SalesData.id).label("order_count")
    ).join(Warehouse, SalesData.warehouse_id == Warehouse.id)
    .group_by(Warehouse.region)
    
    result = await session.execute(query)
    return [dict(row._mapping) for row in result]

# 3. Router (app/routers/sales_router.py)
@router.get("/revenue-by-region", response_model=list[RevenueByRegionResponse])
async def get_revenue_by_region():
    async with async_session() as session:
        data = await sales_service.get_revenue_by_region(session)
    return data

# 4. Test (tests/test_sales.py)
@pytest.mark.asyncio
async def test_get_revenue_by_region(session):
    # insert test data, call service, assert results
```

### Pattern 2: Adding a Database Table

**Example: Adding `production_waste` table**

```bash
# 1. Create migration
alembic revision -m "add production_waste table"

# 2. Edit alembic/versions/xxxxx_add_production_waste_table.py
def upgrade():
    op.create_table(
        'production_waste',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('date', sa.Date),
        sa.Column('waste_kg', sa.Float),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('production_waste')

# 3. Run migration
alembic upgrade head

# 4. Add model (app/models/production.py)
class ProductionWaste(Base):
    __tablename__ = "production_waste"
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date]
    waste_kg: Mapped[float]
    created_at: Mapped[datetime]

# 5. Add service, router, schema
```

### Pattern 3: Syncing from Gateway

**Example: Hourly sales sync**

```python
# In services/sales_service.py
async def sync_from_gateway(self, session: AsyncSession) -> None:
    """Fetch latest sales from Gateway and store in database."""
    logger.info("sales_sync_started")
    
    try:
        # 1. Call gateway
        data = await gateway_client.get("/sales/latest")
        
        # 2. Parse and validate with schema
        sales_list = [SalesCreateRequest(**item) for item in data]
        
        # 3. Store in database (upsert pattern)
        for sale_data in sales_list:
            existing = await session.execute(
                select(SalesData).where(SalesData.external_id == sale_data.external_id)
            )
            existing_obj = existing.scalars().first()
            
            if existing_obj:
                existing_obj.amount = sale_data.amount
                existing_obj.updated_at = datetime.now()
            else:
                session.add(SalesData(**sale_data.model_dump()))
        
        await session.commit()
        logger.info("sales_sync_completed", count=len(sales_list))
    
    except Exception as e:
        await session.rollback()
        logger.error("sales_sync_failed", error=str(e), exc_info=True)
        raise
```

---

## Performance Considerations

### Index Strategy

Add indexes on frequently-filtered columns:

```python
# In models/sales.py
class SalesData(Base):
    __tablename__ = "sales_data"
    
    date: Mapped[datetime.date] = mapped_column(index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
```

### Query Optimization

1. **Eager load relationships** to avoid N+1 queries:
   ```python
   query = select(SalesData).options(joinedload(SalesData.product))
   ```

2. **Filter before aggregation:**
   ```python
   # Good: filter then sum
   query = select(func.sum(SalesData.amount)).where(SalesData.date > start_date)
   
   # Bad: sum everything then filter
   total = await fetch_all_sales()  # ← don't do this
   ```

3. **Use pagination for large result sets:**
   ```python
   page_size = 100
   offset = (page - 1) * page_size
   query = select(...).offset(offset).limit(page_size)
   ```

### Caching Considerations

**No in-memory caching without invalidation strategy.** If you add caching:
- Document how it's invalidated
- Include TTL
- Test cache misses don't break functionality

---

## Logging

All logging uses `structlog` with JSON output. Never use `print()`.

```python
import structlog

logger = structlog.get_logger()

# Log events
logger.info("sales_sync_started", interval_minutes=60)
logger.warning("slow_query", duration_ms=5000, query="...")
logger.error("sync_failed", error="timeout", retry_count=3, exc_info=True)
```

**Structured fields are queryable in production logging:**
- Search: `error="timeout"` to find all timeout errors
- Aggregate: Group by `user_id` to find heavy users
- Alert: Notify when `sync_failed` count > threshold

---

## Deployment

### Docker Image

Built and run via docker-compose. No special deployment logic needed beyond:

1. Environment variables set in `.env`
2. Database migrations run: `alembic upgrade head`
3. App starts: `uvicorn app.main:app --host 0.0.0.0`

### Health Check

Endpoint: `GET /health`

Returns `{"status": "ok"}` if:
- Database connection is alive
- Cron scheduler is running
- No critical errors in last minute

---

## Tech Debt & Known Limitations

### Current

1. **No authentication** — v1 APIs are read-only; auth layer planned for v2
2. **Single-zone database** — No replication yet; single PostgreSQL instance
3. **No caching** — All queries hit the database; Redis integration planned
4. **Limited retention** — Data older than 90 days is deleted (configurable)

### Roadmap

- [ ] API authentication (JWT)
- [ ] Cache layer (Redis)
- [ ] Database replication
- [ ] Metrics export (Prometheus)
- [ ] Rate limiting

---

## When to Ask Questions

- **Not sure how to extend a domain?** → Read the existing domain first, follow its pattern
- **Need to change a core pattern?** → Document the decision in your commit message
- **Want to add a new technology?** → Ask first; discuss tradeoffs
- **Found a limitation?** → Add it to this file under "Known Limitations"

---

**Last updated:** 2026-05-07  
**Architecture version:** 1.0
