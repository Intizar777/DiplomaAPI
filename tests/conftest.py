"""
Pytest configuration and fixtures for testcontainers-based testing.

All tests use a real PostgreSQL database via testcontainers for isolation
and accuracy. Each test gets a clean schema.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from testcontainers.postgres import PostgresContainer

from app.models import Base


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
    sync_url = postgres_container.get_connection_string()
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


@pytest_asyncio.fixture
async def db_session_with_data(session):
    """Provide a session with sample data pre-inserted (for integration tests)."""
    # Subclasses/individual tests can add data here
    yield session
