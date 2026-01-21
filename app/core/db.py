import ssl
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from .config import settings


class Base(DeclarativeBase):
    pass


# Crear contexto SSL para Render
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  # Render confía en su certificado
ssl_context.verify_mode = ssl.CERT_NONE  # No verificar certificado, suficiente para Render

# Engine ASYNC con asyncpg y SSL
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=0,
    connect_args={"ssl": ssl_context},  # 👈 clave para evitar el error
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata_.create_all)


async def close_db() -> None:
    await engine.dispose()
