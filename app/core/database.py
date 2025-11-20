"""
Database connection pool management using asyncpg.
Provides connection lifecycle management and helper methods for query execution.
"""
import json
from typing import Optional, Any, List, Dict
from contextlib import asynccontextmanager

import asyncpg

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class Database:
    """
    Database connection pool manager.
    Handles PostgreSQL connection lifecycle and provides query execution methods.
    """

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """
        Create database connection pool.
        Called during application startup.
        """
        async def init_connection(conn):
            """Initialize connection with custom type codecs."""
            await conn.set_type_codec(
                'jsonb', encoder=json.dumps, decoder=json.loads, schema='pg_catalog'
            )

        try:
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=settings.DATABASE_POOL_MIN_SIZE,
                max_size=settings.DATABASE_POOL_MAX_SIZE,
                command_timeout=60,
                init=init_connection,
            )
            logger.info(
                "database_connected",
                pool_min_size=settings.DATABASE_POOL_MIN_SIZE,
                pool_max_size=settings.DATABASE_POOL_MAX_SIZE,
            )
        except Exception as e:
            logger.error("database_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """
        Close database connection pool.
        Called during application shutdown.
        """
        if self.pool:
            await self.pool.close()
            logger.info("database_disconnected")

    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """
        Execute query and return single row as dictionary.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Dictionary with row data or None if no results
        """
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Execute query and return all rows as list of dictionaries.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            List of dictionaries with row data
        """
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query, *args)
            return [dict(row) for row in rows]

    async def execute(self, query: str, *args) -> str:
        """
        Execute query without returning results (INSERT/UPDATE/DELETE).

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Status string from database
        """
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch_val(self, query: str, *args) -> Any:
        """
        Execute query and return single value.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single value from query result
        """
        async with self.pool.acquire() as connection:
            return await connection.fetchval(query, *args)

    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for database transactions.

        Usage:
            async with db.transaction():
                await db.execute("INSERT ...")
                await db.execute("UPDATE ...")
        """
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                yield connection

    async def health_check(self) -> bool:
        """
        Check database connectivity.

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            result = await self.fetch_val("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e))
            return False


# Global database instance
db = Database()


async def get_db() -> Database:
    """
    Dependency function to get database instance.
    Used for FastAPI dependency injection.

    Returns:
        Database instance
    """
    return db
