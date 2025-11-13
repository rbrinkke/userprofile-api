"""
Redis cache manager for user profiles, settings, and interests.
Implements caching strategy with TTL configuration and cache invalidation logic.
"""
import json
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as redis

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CacheManager:
    """
    Redis cache manager with support for different cache types and TTLs.
    Handles serialization/deserialization and cache invalidation.
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Establish Redis connection. Called during application startup."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                db=settings.REDIS_CACHE_DB,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("redis_cache_connected", db=settings.REDIS_CACHE_DB)
        except Exception as e:
            logger.error("redis_cache_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close Redis connection. Called during application shutdown."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("redis_cache_disconnected")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Deserialized value or None if not found
        """
        if not settings.CACHE_ENABLED or not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                logger.debug("cache_hit", key=key)
                return json.loads(value)
            logger.debug("cache_miss", key=key)
            return None
        except Exception as e:
            logger.error("cache_get_failed", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if not settings.CACHE_ENABLED or not self.redis_client:
            return False

        try:
            ttl = ttl or settings.CACHE_DEFAULT_TTL
            serialized = json.dumps(value, default=str)  # default=str handles UUID, datetime
            await self.redis_client.setex(key, ttl, serialized)
            logger.debug("cache_set", key=key, ttl=ttl)
            return True
        except Exception as e:
            logger.error("cache_set_failed", key=key, error=str(e))
            return False

    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys from cache.

        Args:
            *keys: Cache keys to delete

        Returns:
            Number of keys deleted
        """
        if not settings.CACHE_ENABLED or not self.redis_client or not keys:
            return 0

        try:
            count = await self.redis_client.delete(*keys)
            logger.debug("cache_deleted", keys=list(keys), count=count)
            return count
        except Exception as e:
            logger.error("cache_delete_failed", keys=list(keys), error=str(e))
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not settings.CACHE_ENABLED or not self.redis_client:
            return False

        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error("cache_exists_failed", key=key, error=str(e))
            return False

    # ========================================================================
    # High-level cache methods for specific resources
    # ========================================================================

    async def get_user_profile(self, user_id: UUID) -> Optional[dict]:
        """Get cached user profile."""
        key = f"user_profile:{user_id}"
        return await self.get(key)

    async def set_user_profile(self, user_id: UUID, profile: dict) -> bool:
        """Cache user profile with 5-minute TTL."""
        key = f"user_profile:{user_id}"
        return await self.set(key, profile, ttl=settings.CACHE_TTL_USER_PROFILE)

    async def invalidate_user_profile(self, user_id: UUID) -> int:
        """Invalidate user profile cache."""
        key = f"user_profile:{user_id}"
        return await self.delete(key)

    async def get_user_settings(self, user_id: UUID) -> Optional[dict]:
        """Get cached user settings."""
        key = f"user_settings:{user_id}"
        return await self.get(key)

    async def set_user_settings(self, user_id: UUID, settings: dict) -> bool:
        """Cache user settings with 30-minute TTL."""
        key = f"user_settings:{user_id}"
        return await self.set(key, settings, ttl=settings.CACHE_TTL_USER_SETTINGS)

    async def invalidate_user_settings(self, user_id: UUID) -> int:
        """Invalidate user settings cache."""
        key = f"user_settings:{user_id}"
        return await self.delete(key)

    async def get_user_interests(self, user_id: UUID) -> Optional[list]:
        """Get cached user interests."""
        key = f"user_interests:{user_id}"
        return await self.get(key)

    async def set_user_interests(self, user_id: UUID, interests: list) -> bool:
        """Cache user interests with 1-hour TTL."""
        key = f"user_interests:{user_id}"
        return await self.set(key, interests, ttl=settings.CACHE_TTL_USER_INTERESTS)

    async def invalidate_user_interests(self, user_id: UUID) -> int:
        """Invalidate user interests cache."""
        key = f"user_interests:{user_id}"
        return await self.delete(key)

    async def invalidate_all_user_caches(self, user_id: UUID) -> int:
        """
        Invalidate all caches related to a user.
        Called on profile updates, account deletion, etc.
        """
        keys = [
            f"user_profile:{user_id}",
            f"user_settings:{user_id}",
            f"user_interests:{user_id}",
        ]
        return await self.delete(*keys)

    async def health_check(self) -> bool:
        """Check Redis connectivity for health endpoint."""
        try:
            if self.redis_client:
                return await self.redis_client.ping()
            return False
        except Exception as e:
            logger.error("redis_health_check_failed", error=str(e))
            return False


# Global cache manager instance
cache = CacheManager()


async def get_cache() -> CacheManager:
    """
    Dependency function to get cache manager instance.
    Used for FastAPI dependency injection.
    """
    return cache
