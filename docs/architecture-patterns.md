# Architecture Patterns

Reference guide for common implementation patterns in DiplomaAPI. Each pattern includes code examples and explains the "why" behind the approach.

---

## Pattern 1: Adding a New Endpoint

**When:** You need to add a GET endpoint that queries the database and returns data.

**Three-step process:**
1. Define the Pydantic schema (request/response)
2. Write the service method with business logic
3. Add the thin route that delegates to the service

### Example: KPI Current Endpoint

**Step 1: Define the schema**

```python
# app/schemas/kpi.py
from pydantic import BaseModel, Field
from datetime import datetime

class KPICurrentResponse(BaseModel):
    id: int
    production_line: str
    throughput: float = Field(..., description="Units per hour")
    uptime_percent: float
    timestamp: datetime
    
    class Config:
        from_attributes = True  # Map ORM model attributes to schema fields
```

**Step 2: Write the service method**

```python
# app/services/kpi_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.kpi import KPIData
import structlog

logger = structlog.get_logger()

class KPIService:
    async def get_current_kpi(self, session: AsyncSession) -> list[KPIData]:
        """
        Fetch the latest KPI reading for each production line.
        
        Returns: List of KPI records ordered by most recent first.
        """
        result = await session.execute(
            select(KPIData)
            .order_by(KPIData.recorded_at.desc())
            .limit(1)
        )
        kpi_list = result.scalars().all()
        logger.info("kpi_fetched", count=len(kpi_list))
        return kpi_list
```

**Step 3: Add the route**

```python
# app/routers/kpi_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.kpi_service import KPIService
from app.schemas.kpi import KPICurrentResponse

router = APIRouter(prefix="/api/v1/kpi", tags=["kpi"])
kpi_service = KPIService()

@router.get("/current", response_model=list[KPICurrentResponse])
async def get_current_kpi(
    session: AsyncSession = Depends(get_db)
) -> list[KPICurrentResponse]:
    """
    Get current KPI metrics for all production lines.
    
    Returns the most recent KPI reading.
    """
    data = await kpi_service.get_current_kpi(session)
    return data  # Pydantic serializes ORM models via from_attributes=True
```

**Step 4: Write tests for the service**

```python
# tests/unit/test_kpi_service.py
import pytest
from datetime import datetime
from app.models.kpi import KPIData
from app.services.kpi_service import KPIService

@pytest.mark.asyncio
async def test_get_current_kpi_returns_latest(session):
    """Service returns the most recent KPI entry."""
    # Insert test data
    old_kpi = KPIData(production_line="A1", throughput=100, uptime_percent=99.5, recorded_at=datetime(2026, 5, 1))
    new_kpi = KPIData(production_line="A1", throughput=105, uptime_percent=99.8, recorded_at=datetime(2026, 5, 7))
    session.add(old_kpi)
    session.add(new_kpi)
    await session.commit()
    
    # Call service
    service = KPIService()
    result = await service.get_current_kpi(session)
    
    # Assert returns latest
    assert len(result) == 1
    assert result[0].throughput == 105
    assert result[0].recorded_at == datetime(2026, 5, 7)
```

**Step 5: Test the route** (optional if service is thoroughly tested)

```python
# tests/integration/test_kpi_routes.py
@pytest.mark.asyncio
async def test_kpi_current_route_returns_json(client, session):
    """HTTP endpoint returns valid JSON response."""
    # Insert test data
    session.add(KPIData(production_line="A1", throughput=100, uptime_percent=99.5))
    await session.commit()
    
    # Call endpoint
    response = await client.get("/api/v1/kpi/current")
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["production_line"] == "A1"
```

**Why this pattern works:**
- Schema enforces input validation and documents the API contract
- Service method contains all business logic (testable and reusable)
- Route is thin (3 lines) and just delegates to the service
- Tests focus on the service; route tests are redundant

---

## Pattern 2: Adding a New Database Table

**When:** You need to store a new type of data (e.g., a new domain like "Sensors" or "Output").

**Three steps:**
1. Create the ORM model
2. Create an Alembic migration
3. Implement the service and routes

### Example: Adding a Sensor Data Table

**Step 1: Create the model**

```python
# app/models/sensor.py
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id: int = Column(Integer, primary_key=True)
    sensor_id: str = Column(String(50), nullable=False, unique=True)
    sensor_name: str = Column(String(100), nullable=False)
    temperature: float = Column(Float, nullable=True)
    pressure: float = Column(Float, nullable=True)
    recorded_at: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    def __repr__(self):
        return f"<SensorData(sensor_id={self.sensor_id}, temperature={self.temperature})>"
```

**Step 2: Create a migration**

```bash
alembic revision -m "add sensor_data table"
```

This creates a file like `alembic/versions/001_add_sensor_data_table.py`.

**Step 3: Edit the migration file**

```python
# alembic/versions/001_add_sensor_data_table.py
"""add sensor_data table."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Identifies the schema version
revision = '001'
down_revision = None

def upgrade():
    """Create sensor_data table."""
    op.create_table(
        'sensor_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sensor_id', sa.String(length=50), nullable=False),
        sa.Column('sensor_name', sa.String(length=100), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('pressure', sa.Float(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sensor_id', name='uq_sensor_data_sensor_id')
    )

def downgrade():
    """Drop sensor_data table."""
    op.drop_table('sensor_data')
```

**Step 4: Run the migration**

```bash
alembic upgrade head
```

Verify the table exists:
```bash
psql -d <database_url> -c "\dt"
```

**Step 5: Create service methods**

```python
# app/services/sensor_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sensor import SensorData
import structlog

logger = structlog.get_logger()

class SensorService:
    async def get_sensor_readings(
        self, 
        session: AsyncSession,
        limit: int = 100
    ) -> list[SensorData]:
        """Fetch latest sensor readings."""
        result = await session.execute(
            select(SensorData)
            .order_by(SensorData.recorded_at.desc())
            .limit(limit)
        )
        readings = result.scalars().all()
        logger.info("sensor_readings_fetched", count=len(readings))
        return readings
    
    async def sync_sensor_readings_from_gateway(self, session: AsyncSession) -> None:
        """Fetch sensor data from Gateway API and upsert into database."""
        try:
            gateway_data = await gateway_client.get("/sensors/readings")
            
            for item in gateway_data:
                existing = await session.execute(
                    select(SensorData).where(SensorData.sensor_id == item["sensor_id"])
                )
                sensor = existing.scalar_one_or_none()
                
                if sensor:
                    sensor.temperature = item.get("temperature")
                    sensor.pressure = item.get("pressure")
                else:
                    session.add(SensorData(
                        sensor_id=item["sensor_id"],
                        sensor_name=item["name"],
                        temperature=item.get("temperature"),
                        pressure=item.get("pressure")
                    ))
            
            await session.commit()
            logger.info("sensor_sync_completed", count=len(gateway_data))
        except Exception as e:
            logger.error("sensor_sync_failed", error=str(e))
            raise
```

**Why this pattern works:**
- Migrations are versioned and reversible; never edit them after commit
- Models are SQLAlchemy ORM objects, not raw SQL
- Sync methods keep data fresh hourly

---

## Pattern 3: Syncing Data from Gateway API

**When:** You need to pull data from the external EFKO Gateway API and store it in PostgreSQL.

**The sync method pattern:**

```python
# app/services/sales_service.py
from app.services.gateway_client import gateway_client
import structlog

logger = structlog.get_logger()

class SalesService:
    async def sync_sales_from_gateway(self, session: AsyncSession) -> None:
        """
        Fetch latest sales from Gateway API and upsert into database.
        
        Called hourly by APScheduler. If sync fails, error is logged and scheduler continues.
        """
        try:
            # 1. Fetch from Gateway
            gateway_data = await gateway_client.get("/sales/latest")
            logger.info("gateway_fetch_success", endpoint="/sales/latest", count=len(gateway_data))
            
            # 2. Upsert: insert if new, update if exists
            for item in gateway_data:
                # Check if record exists
                db_record = await session.execute(
                    select(SalesData).where(SalesData.source_id == item["id"])
                )
                existing_sale = db_record.scalar_one_or_none()
                
                if existing_sale:
                    # Update existing record
                    existing_sale.amount = item["amount"]
                    existing_sale.region = item["region"]
                    existing_sale.recorded_at = datetime.fromisoformat(item["timestamp"])
                    logger.info("sales_record_updated", source_id=item["id"])
                else:
                    # Insert new record
                    session.add(SalesData(
                        source_id=item["id"],
                        amount=item["amount"],
                        product_id=item["product_id"],
                        region=item["region"],
                        recorded_at=datetime.fromisoformat(item["timestamp"])
                    ))
                    logger.info("sales_record_inserted", source_id=item["id"])
            
            # 3. Commit all changes
            await session.commit()
            logger.info("sales_sync_completed", count=len(gateway_data))
            
        except HTTPError as e:
            logger.error("gateway_http_error", status=e.status_code, error=str(e))
            # Don't re-raise; let scheduler continue
        except Exception as e:
            logger.error("sales_sync_failed", error=str(e))
            # Don't re-raise; let scheduler continue
```

**How the cron scheduler calls this:**

```python
# app/cron/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
import structlog

logger = structlog.get_logger()

def start_scheduler(app: FastAPI):
    """Start the background scheduler for hourly syncs."""
    scheduler = BackgroundScheduler()
    
    # Schedule sync jobs to run every 60 minutes
    scheduler.add_job(
        sync_all_data,
        trigger="interval",
        minutes=60,
        id="sync_all_data",
        name="Sync all data from Gateway"
    )
    
    scheduler.start()
    logger.info("scheduler_started", jobs=len(scheduler.get_jobs()))
    
    # Store scheduler in app state for shutdown
    app.state.scheduler = scheduler

async def sync_all_data():
    """Called hourly: sync all domains from Gateway."""
    logger = structlog.get_logger()
    
    async with get_db() as session:
        try:
            await kpi_service.sync_kpi_from_gateway(session)
            await sales_service.sync_sales_from_gateway(session)
            await order_service.sync_orders_from_gateway(session)
            await quality_service.sync_quality_from_gateway(session)
            await inventory_service.sync_inventory_from_gateway(session)
            logger.info("all_syncs_completed")
        except Exception as e:
            logger.error("sync_batch_failed", error=str(e))
```

**Why this pattern works:**
- Sync methods are idempotent (safe to call multiple times)
- Errors are logged but don't stop the scheduler
- Upsert logic handles both new and existing records
- All changes are committed together

---

## Pattern 4: Enriching Data with JOINs

**When:** You need to add related data (e.g., `product_name`) to your response.

**The JOIN pattern:**

```python
# ✅ Good: One query, all data joined
async def get_sales_with_product_names(self, session: AsyncSession) -> list[dict]:
    """Fetch sales with product names via JOIN."""
    result = await session.execute(
        select(
            SalesData.id,
            SalesData.amount,
            SalesData.recorded_at,
            Product.name.label("product_name"),  # Joined data
            Product.sku.label("product_sku")     # Joined data
        ).join(
            Product,
            SalesData.product_id == Product.id
        )
        .order_by(SalesData.recorded_at.desc())
    )
    return [row._mapping for row in result.all()]
```

**In your schema:**

```python
# app/schemas/sales.py
from pydantic import BaseModel
from decimal import Decimal

class SalesWithProductResponse(BaseModel):
    id: int
    amount: Decimal
    recorded_at: datetime
    product_name: str        # Comes from JOIN
    product_sku: str         # Comes from JOIN
```

**In your route:**

```python
# app/routers/sales_router.py
@router.get("/with-products", response_model=list[SalesWithProductResponse])
async def get_sales_with_products(
    session: AsyncSession = Depends(get_db)
):
    """Get sales with product enrichment."""
    data = await sales_service.get_sales_with_product_names(session)
    return data
```

---

### ⚠️ Gotcha: UUID to varchar JOIN

If `product_id` is UUID and `Product.source_system_id` is varchar, you must cast:

```python
from sqlalchemy import cast, String

# ❌ This fails: "operator does not exist: uuid = character varying"
result = await session.execute(
    select(SalesData, Product.name).join(
        Product,
        SalesData.product_id == Product.source_system_id  # Type mismatch!
    )
)

# ✅ This works: Cast UUID to String
result = await session.execute(
    select(SalesData, Product.name).join(
        Product,
        cast(SalesData.product_id, String) == Product.source_system_id
    )
)
```

**Why the cast is needed:**
- PostgreSQL/asyncpg enforces strict type matching
- UUID columns cannot implicitly cast to varchar
- The `cast(col, String)` function converts the UUID to string for comparison

---

### ❌ Don't Do N+1 Loops

```python
# ❌ WRONG: This runs 100+ queries (N+1 problem)
sales = await fetch_all_sales()  # Query 1
for sale in sales:
    product = await fetch_product(sale.product_id)  # Query 2, 3, 4, ... N
    sale.product_name = product.name
```

**Why it's bad:**
- 100 sales = 101 database round-trips
- Very slow as data grows
- Network latency multiplied by N

**Use a JOIN instead (1 query):**
```python
# ✅ RIGHT: One query with JOIN
result = await session.execute(
    select(SalesData, Product.name).join(Product)
)
```

---

## Pattern 5: Query by Date Range

**When:** You need to filter data by a date range (e.g., "last 7 days" or "between two dates").

**The schema:**

```python
# app/schemas/common.py
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

class DateRangeParams(BaseModel):
    """Query parameters for date filtering."""
    date_from: datetime = Field(
        default_factory=lambda: datetime.now() - timedelta(days=30),
        alias="date_from",
        description="Start date (default: 30 days ago)"
    )
    to: datetime = Field(
        default_factory=datetime.now,
        alias="to",
        description="End date (default: today)"
    )
    
    class Config:
        populate_by_name = True  # Allow both field name and alias
```

**In your route:**

```python
# app/routers/kpi_router.py
@router.get("/history", response_model=list[KPIHistoryResponse])
async def get_kpi_history(
    params: DateRangeParams = Depends(),  # Query params become DateRangeParams
    session: AsyncSession = Depends(get_db)
):
    """Get KPI data for a date range."""
    data = await kpi_service.get_kpi_history(session, params.date_from, params.to)
    return data
```

**In your service:**

```python
# app/services/kpi_service.py
async def get_kpi_history(
    self,
    session: AsyncSession,
    date_from: datetime,
    to: datetime
) -> list[KPIData]:
    """Fetch KPI records between two dates."""
    result = await session.execute(
        select(KPIData).where(
            (KPIData.recorded_at >= date_from) &
            (KPIData.recorded_at <= to)
        )
        .order_by(KPIData.recorded_at.desc())
    )
    return result.scalars().all()
```

**In your test:**

```python
# tests/integration/test_kpi_routes.py
@pytest.mark.asyncio
async def test_kpi_history_with_date_range(client, session):
    """Endpoint filters by date range."""
    # Insert test data
    session.add(KPIData(recorded_at=datetime(2026, 5, 1), throughput=100))
    session.add(KPIData(recorded_at=datetime(2026, 5, 7), throughput=105))
    session.add(KPIData(recorded_at=datetime(2026, 5, 15), throughput=110))
    await session.commit()
    
    # Query with date range: May 5 to May 10
    response = await client.get(
        "/api/v1/kpi/history?date_from=2026-05-05&to=2026-05-10"
    )
    
    # Should return only the May 7 entry
    data = response.json()
    assert len(data) == 1
    assert data[0]["throughput"] == 105
```

**⚠️ Gotcha: Use `date_from`, not `from`**

```python
# ❌ This does NOT work (from is a Python keyword)
GET /api/v1/kpi/history?from=2026-05-01&to=2026-05-07

# ✅ This works
GET /api/v1/kpi/history?date_from=2026-05-01&to=2026-05-07
```

Why? FastAPI cannot pass `from` as a keyword argument to the function because it's a Python keyword.

---

## Pattern 6: Async Testing with Testcontainers

**When:** You need to write unit and integration tests that use a real PostgreSQL database.

**Setup in conftest.py:**

```python
# tests/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient

# Global container (reused for all tests in session)
postgres_container = None

@pytest.fixture(scope="session")
def postgres_db():
    """Spin up a PostgreSQL container for the entire test session."""
    global postgres_container
    postgres_container = PostgresContainer("postgres:14")
    postgres_container.start()
    yield postgres_container
    postgres_container.stop()

@pytest.fixture
async def session(postgres_db):
    """Create a fresh async database session for each test."""
    # Connect to test database
    engine = create_async_engine(
        postgres_db.get_connection_url().replace("psycopg2", "asyncpg"),
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session maker
    SessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Yield a fresh session
    async with SessionLocal() as db_session:
        yield db_session
    
    # Cleanup: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def client(session):
    """Create an async HTTP client for testing FastAPI routes."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    # Override get_db dependency for tests
    async def override_get_db():
        yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Use AsyncClient with ASGI transport
    from httpx import ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    # Cleanup
    app.dependency_overrides.clear()
```

**Unit test (service logic):**

```python
# tests/unit/test_sales_service.py
import pytest
from datetime import datetime
from app.models.sales import SalesData
from app.services.sales_service import SalesService

@pytest.mark.asyncio
async def test_sales_service_get_top_products(session):
    """Service returns products sorted by total amount."""
    # Insert test data
    session.add(SalesData(product_id=1, amount=100, recorded_at=datetime.now()))
    session.add(SalesData(product_id=1, amount=50, recorded_at=datetime.now()))
    session.add(SalesData(product_id=2, amount=30, recorded_at=datetime.now()))
    await session.commit()
    
    # Call service
    service = SalesService()
    result = await service.get_top_products(session, limit=1)
    
    # Assert
    assert len(result) == 1
    assert result[0].product_id == 1
    assert result[0].total_amount == 150
```

**Integration test (route):**

```python
# tests/integration/test_sales_routes.py
@pytest.mark.asyncio
async def test_sales_summary_route(client, session):
    """HTTP endpoint returns valid JSON response."""
    # Insert test data
    session.add(SalesData(product_id=1, amount=100, recorded_at=datetime.now()))
    await session.commit()
    
    # Call endpoint
    response = await client.get("/api/v1/sales/summary")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "total_amount" in data
    assert data["total_amount"] == 100
```

**Why testcontainers:**
- Real PostgreSQL database (not mocked)
- Each test gets a fresh, clean database
- Tests are isolated and can run in parallel
- No Docker setup required by user

---

## Pattern 7: Error Handling with Specific HTTP Codes

**When:** You need to return appropriate HTTP status codes based on what went wrong.

**The pattern:**

```python
# app/routers/orders_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.orders import OrderData
from app.schemas.orders import OrderResponse
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: int,
    session: AsyncSession = Depends(get_db)
):
    """
    Get order by ID.
    
    Returns:
        - 200: Order found and returned
        - 404: Order not found
        - 500: Database error
    """
    try:
        # Query database
        result = await session.execute(
            select(OrderData).where(OrderData.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        # Resource not found
        if not order:
            logger.warning("order_not_found", order_id=order_id)
            raise HTTPException(
                status_code=404,
                detail=f"Order {order_id} not found"
            )
        
        logger.info("order_retrieved", order_id=order_id)
        return order
        
    except SQLAlchemyError as e:
        # Database error
        logger.error("database_error", order_id=order_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Database error; check server logs"
        )
    except Exception as e:
        # Unexpected error
        logger.error("unexpected_error", order_id=order_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Unexpected error; check server logs"
        )
```

**HTTP Status Codes to Use:**

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Record found and returned |
| 400 | Bad request | Invalid query parameters |
| 404 | Not found | Order ID doesn't exist |
| 422 | Validation error | Invalid schema (Pydantic handles this) |
| 500 | Server error | Database connection failed |

**In tests:**

```python
# tests/integration/test_order_routes.py
@pytest.mark.asyncio
async def test_get_order_not_found(client):
    """Returns 404 when order doesn't exist."""
    response = await client.get("/api/v1/orders/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_order_success(client, session):
    """Returns 200 with order data when found."""
    session.add(OrderData(id=1, customer_name="Alice", total=100.00))
    await session.commit()
    
    response = await client.get("/api/v1/orders/1")
    assert response.status_code == 200
    data = response.json()
    assert data["customer_name"] == "Alice"
```

---

## Summary

These seven patterns cover the majority of work in DiplomaAPI:

1. **New endpoint** → Start with schema, write service, add route, test service
2. **New table** → Model, migration, implement service methods
3. **Gateway sync** → Async method with upsert, called hourly by cron
4. **Enrich with JOIN** → Use single query with JOIN, not N+1 loops
5. **Date filtering** → Use `DateRangeParams` schema, filter in service
6. **Testing** → Testcontainers for real DB, async fixtures, test services not routes
7. **Error handling** → Return specific HTTP codes, log errors, handle exceptions

For more details, see:
- `CLAUDE.md` — Architecture overview
- `AGENTS.md` — Working rules and startup checklist
- `feature_list.json` — Feature status and evidence
- `progress.md` — Prior session context

---

**Last updated:** 2026-05-07
