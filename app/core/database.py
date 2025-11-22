"""
Database connection management using SQLModel and SQLAlchemy.
Provides asynchronous session management.
"""
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Create Async Engine
# Convert postgresql:// to postgresql+asyncpg:// if necessary
database_url = settings.DATABASE_URL
if database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    database_url,
    echo=False,  # Set to True for SQL logging
    future=True,
    pool_size=settings.DATABASE_POOL_MIN_SIZE,
    max_overflow=settings.DATABASE_POOL_MAX_SIZE,
    pool_pre_ping=True,
)

# Create Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def connect() -> None:
    """
    Establish database connection.
    """
    try:
        # Create tables if they don't exist (optional, usually handled by migrations)
        # async with engine.begin() as conn:
        #     await conn.run_sync(SQLModel.metadata.create_all)

        logger.info("database_connected")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        raise

async def disconnect() -> None:
    """
    Close database connection.
    """
    await engine.dispose()
    logger.info("database_disconnected")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("session_rollback", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()

async def health_check() -> bool:
    """
    Check database connectivity.
    """
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False
