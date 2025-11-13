"""Interest Service - Handles interest tags management."""
from typing import List
from uuid import UUID
from app.core.cache import cache
from app.core.database import db
from app.core.exceptions import ResourceNotFoundError, ResourceLimitExceededError
from app.core.logging_config import get_logger
from app.schemas.common import InterestTag

logger = get_logger(__name__)

class InterestService:
    """Service for interest tags operations."""

    async def get_interests(self, user_id: UUID) -> List[InterestTag]:
        """Get user interests."""
        cached = await cache.get_user_interests(user_id)
        if cached:
            return [InterestTag(**i) for i in cached]

        rows = await db.fetch_all(
            "SELECT interest_tag as tag, weight FROM activity.user_interests WHERE user_id = $1",
            user_id
        )
        interests = [InterestTag(**row) for row in rows]
        await cache.set_user_interests(user_id, [i.dict() for i in interests])
        return interests

    async def set_interests(self, user_id: UUID, interests: List[InterestTag]) -> tuple[bool, int]:
        """Set all interests (replaces existing)."""
        import json
        interests_json = json.dumps([i.dict() for i in interests])

        result = await db.fetch_one(
            "SELECT * FROM activity.sp_set_user_interests($1, $2::jsonb)",
            user_id, interests_json
        )

        if not result["success"]:
            raise ResourceLimitExceededError(resource="interests", limit=20)

        await cache.invalidate_user_interests(user_id)
        await cache.invalidate_user_profile(user_id)
        logger.info("interests_set", user_id=str(user_id), count=result["interest_count"])
        return result["success"], result["interest_count"]

    async def add_interest(self, user_id: UUID, tag: str, weight: float) -> bool:
        """Add single interest."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_add_user_interest($1, $2, $3)",
            user_id, tag, weight
        )

        if not result["success"]:
            if "Maximum" in result["message"]:
                raise ResourceLimitExceededError(resource="interests", limit=20)
            raise ResourceNotFoundError(resource="User")

        await cache.invalidate_user_interests(user_id)
        await cache.invalidate_user_profile(user_id)
        logger.info("interest_added", user_id=str(user_id), tag=tag)
        return result["success"]

    async def remove_interest(self, user_id: UUID, tag: str) -> bool:
        """Remove single interest."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_remove_user_interest($1, $2)",
            user_id, tag
        )

        await cache.invalidate_user_interests(user_id)
        await cache.invalidate_user_profile(user_id)
        logger.info("interest_removed", user_id=str(user_id), tag=tag)
        return result["success"]

interest_service = InterestService()
