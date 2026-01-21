"""Pytest configuration and fixtures for tests."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.db import Base

# Test database URL (use in-memory SQLite for simplicity)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    Each test gets a fresh database with all tables created.
    After the test, the database is cleaned up.
    """
    # Create async engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata_.create_all)

    # Create session factory
    async_session_maker = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create session
    async with async_session_maker() as session:
        yield session

    # Cleanup: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata_.drop_all)

    await engine.dispose()
