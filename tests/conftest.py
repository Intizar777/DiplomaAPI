"""
Pytest configuration and fixtures for testcontainers-based testing.

All tests use a real PostgreSQL database via testcontainers for isolation
and accuracy. Each test gets a clean schema.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from testcontainers.postgres import PostgresContainer
from faker import Faker

from app.models import Base
from app.models.product import Product
from app.models.sales import AggregatedSales, SalesTrends
from app.models.kpi import AggregatedKPI
from fastapi.testclient import TestClient
from app.main import app

fake = Faker()


@pytest.fixture(scope="session")
def postgres_container():
    """Start a PostgreSQL container for the entire test session."""
    container = PostgresContainer("postgres:14")
    container.start()
    yield container
    container.stop()


@pytest_asyncio.fixture
async def test_engine(postgres_container):
    """Create an async SQLAlchemy engine connected to the test database."""
    # Convert psycopg2 URL from testcontainers to asyncpg URL
    sync_url = postgres_container.get_connection_url()
    async_url = sync_url.replace("psycopg2", "asyncpg")

    engine = create_async_engine(async_url, echo=False)

    # Create all tables from models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def session(test_engine):
    """Provide a test database session for a single test."""
    async with AsyncSession(test_engine, expire_on_commit=False) as s:
        yield s
        # Rollback to keep session clean for next test
        await s.rollback()


@pytest.fixture
def client(session):
    """FastAPI TestClient with test database session."""
    # Note: This is a simplified version; for full integration tests,
    # you'd need to override the database dependency in the app
    return TestClient(app)


@pytest_asyncio.fixture
async def sample_products(session) -> list[Product]:
    """Insert 5 sample products for testing."""
    products = [
        Product(
            code=f"PROD-{fake.bothify(text='###')}",
            name=fake.word(),
            category=fake.random_element(["Electronics", "Food", "Clothing"]),
            brand=fake.word(),
            unit_of_measure="pcs",
            shelf_life_days=fake.random_int(min=30, max=365),
            requires_quality_check=fake.boolean(),
            source_system_id=fake.uuid4()
        )
        for _ in range(5)
    ]
    session.add_all(products)
    await session.commit()
    return products


@pytest_asyncio.fixture
async def sample_sales_data(session, sample_products):
    """Insert sample sales aggregation data."""
    today = date.today()
    sales = []

    for i, product in enumerate(sample_products):
        sales.append(
            AggregatedSales(
                period_from=today - timedelta(days=30),
                period_to=today,
                group_by_type="product",
                group_key=product.code,
                total_quantity=Decimal(fake.random_int(min=10, max=1000)),
                total_amount=Decimal(fake.random_int(min=1000, max=100000)),
                sales_count=fake.random_int(min=5, max=50),
                avg_order_value=Decimal(fake.random_int(min=100, max=10000))
            )
        )

    session.add_all(sales)
    await session.commit()
    return sales


@pytest_asyncio.fixture
async def sample_kpi_data(session):
    """Insert 30 days of KPI data."""
    today = date.today()
    kpi_records = []

    for days_ago in range(0, 30, 10):  # Create KPI records every 10 days
        kpi = AggregatedKPI(
            period_from=today - timedelta(days=days_ago + 10),
            period_to=today - timedelta(days=days_ago),
            production_line=None,
            total_output=Decimal(fake.random_int(min=100, max=5000)),
            defect_rate=Decimal(str(round(fake.random.uniform(0.5, 5.0), 2))),
            completed_orders=fake.random_int(min=20, max=100),
            total_orders=fake.random_int(min=100, max=200),
            oee_estimate=Decimal(str(round(fake.random.uniform(70, 95), 2))))
        kpi_records.append(kpi)

    session.add_all(kpi_records)
    await session.commit()
    return kpi_records


@pytest_asyncio.fixture
async def db_session_with_data(session, sample_products, sample_sales_data, sample_kpi_data):
    """Provide a session with all sample data pre-inserted."""
    yield session
