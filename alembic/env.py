"""Alembic environment configuration with synchronous SQLAlchemy.

Note: Alembic uses a SYNC engine with psycopg2, completely independent
from the async runtime engine (asyncpg) used by FastAPI.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.db import Base

# Import all models to register them with Base.metadata
from app.modules.users.models import User, UserPreferences, UserSession
from app.modules.contracts.models import Contract, ContractVersion, ContractParty, ActivityLog
from app.modules.ai.models import AsyncJob, AICache
from app.modules.signatures.models import Signature, SignatureToken
from app.modules.notifications.models import Invitation, Reminder
from app.modules.audit.models import AuditLog

# Alembic Config object
config = context.config

# Override sqlalchemy.url with SYNC version (psycopg2)
# This converts postgresql+asyncpg:// to postgresql:// automatically
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata_ from Base (only metadata is shared, not the engine)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create a SYNC Engine and associate
    a connection with the context. Uses psycopg2 driver.
    """
    # Create SYNC engine using psycopg2
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


# Run migrations
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
