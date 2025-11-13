"""Subscription Service - Handles subscription management."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.core.cache import cache
from app.core.database import db
from app.core.exceptions import ResourceNotFoundError
from app.core.logging_config import get_logger
from app.schemas.common import SubscriptionLevel

logger = get_logger(__name__)

class SubscriptionService:
    """Service for subscription management."""

    async def get_subscription(self, user_id: UUID) -> dict:
        """Get current subscription details."""
        result = await db.fetch_one(
            "SELECT subscription_level, subscription_expires_at, is_captain, captain_since FROM activity.users WHERE user_id = $1",
            user_id
        )

        if not result:
            raise ResourceNotFoundError(resource="User")

        days_remaining = None
        if result["subscription_expires_at"]:
            delta = result["subscription_expires_at"] - datetime.utcnow()
            days_remaining = max(0, delta.days)

        return {
            "subscription_level": result["subscription_level"],
            "subscription_expires_at": result["subscription_expires_at"],
            "is_captain": result["is_captain"],
            "days_remaining": days_remaining
        }

    async def update_subscription(self, user_id: UUID, subscription_level: SubscriptionLevel, expires_at: Optional[datetime]) -> bool:
        """Update subscription level."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_update_subscription($1, $2, $3)",
            user_id, subscription_level.value, expires_at
        )

        if not result or not result["success"]:
            raise ResourceNotFoundError(resource="User")

        await cache.invalidate_all_user_caches(user_id)
        logger.info("subscription_updated", user_id=str(user_id), level=subscription_level.value)
        return True

    async def set_captain_status(self, user_id: UUID, is_captain: bool) -> bool:
        """Grant/revoke captain status."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_set_captain_status($1, $2)",
            user_id, is_captain
        )

        if not result or not result["success"]:
            raise ResourceNotFoundError(resource="User")

        await cache.invalidate_all_user_caches(user_id)
        logger.info("captain_status_set", user_id=str(user_id), is_captain=is_captain)
        return True

subscription_service = SubscriptionService()
