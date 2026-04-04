# migrations/env.py

# This is the Alembic configuration file.
# It tells Alembic HOW to connect to the database
# and WHERE to find our models.

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import our Base — Alembic needs to see all models
# to know what tables exist
from app.db.base import Base

# Import ALL models here so Alembic can detect them
# Every time you add a new model, add its import here
from app.models.user import User

# Alembic config object
config = context.config

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what Alembic compares against the real DB
# to figure out what changed
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations without a live DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """Run migrations with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,   # don't pool connections during migrations
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    """Entry point for online migrations."""
    asyncio.run(run_async_migrations())

# Alembic calls either offline or online depending on context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()