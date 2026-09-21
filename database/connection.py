"""
NEXUS Database Connection & Session Management
Handles async PostgreSQL/TimescaleDB connection pooling with graceful fallback for local development.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from configs.settings import settings
from database.schemas.models import Base

logger = logging.getLogger("nexus.database")

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine, _sessionmaker
    if _engine is None:
        try:
            db_url = settings.database_url
            # Test if postgres driver or fallback is appropriate
            _engine = create_async_engine(
                db_url,
                echo=False,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
            )
            _sessionmaker = async_sessionmaker(
                bind=_engine,
                expire_on_commit=False,
                class_=AsyncSession,
            )
        except Exception as e:
            logger.warning(f"PostgreSQL connection initialization failed: {e}. Falling back to SQLite async engine.")
            _engine = create_async_engine(
                settings.sqlite_fallback_url,
                echo=False,
            )
            _sessionmaker = async_sessionmaker(
                bind=_engine,
                expire_on_commit=False,
                class_=AsyncSession,
            )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _sessionmaker is not None
    return _sessionmaker


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Initializes the database schema (creates tables if they don't exist)."""
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not connect to primary database ({e}). Initializing SQLite fallback...")
        global _engine, _sessionmaker
        _engine = create_async_engine(settings.sqlite_fallback_url, echo=False)
        _sessionmaker = async_sessionmaker(bind=_engine, expire_on_commit=False, class_=AsyncSession)
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Fallback SQLite database initialized successfully.")
