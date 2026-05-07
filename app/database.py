"""
Database configuration and session management with lifecycle logging.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings
from app.models.base import Base
import structlog

logger = structlog.get_logger()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db():
    """
    Dependency to get database session.
    Usage: async with get_db() as db:
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    logger.info(
        "database_lifecycle",
        phase="initialization",
        action="create_tables",
        database_url=settings.database_url.replace("://", "://***@"),
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(
        "database_lifecycle",
        phase="initialization",
        action="create_tables_complete",
    )


async def close_db():
    """Close database connections."""
    logger.info(
        "database_lifecycle",
        phase="shutdown",
        action="dispose_engine",
    )
    await engine.dispose()
    logger.info(
        "database_lifecycle",
        phase="shutdown",
        action="dispose_engine_complete",
    )
