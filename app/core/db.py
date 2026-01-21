"""Database configuration with SQLAlchemy 2.0 async.

IMPORTANT: This module is for RUNTIME use only (FastAPI application).
- Uses ASYNC engine with asyncpg driver (postgresql+asyncpg://)
- This engine should NEVER be imported by Alembic migrations
- Alembic has its own SYNC engine configuration (psycopg2)
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Note: Only the Base.metadata is shared with Alembic for migrations.
    The engine itself is independent.
    """

    pass


# Create ASYNC engine for FastAPI runtime
# Uses asyncpg driver - NOT used by Alembic
# pool_size=5, max_overflow=0 for Render Free Tier
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=0,  # No overflow on Render Free to avoid silent failures
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
