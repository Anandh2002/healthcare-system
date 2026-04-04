# app/db/session.py

# This file sets up our connection to PostgreSQL.
# Think of it as the "phone line" between FastAPI and the database.

from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine,async_sessionmaker
from app.core.config import settings

# The engine is the actual connection to PostgreSQL.
# "echo=True" prints every SQL query to the console during development
# — very helpful for debugging, turn off in production.

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,         # logs SQL queries when DEBUG=True
    pool_size=10,                # max 10 connections in the pool
    max_overflow=20,             # allow 20 extra connections if pool is full
)

# AsyncSessionLocal is a factory that creates new DB sessions.
# Each request gets its own session — like each customer gets their own waiter.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # don't expire objects after commit (avoids extra queries)
    autocommit=False,         # we control when to commit manually
    autoflush=False,          # we control when to flush manually
)
