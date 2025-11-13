"""Moderation Service - Handles admin moderation operations."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from app.core.cache import cache
from app.core.database import db
from app.core.exceptions import ResourceNotFoundError
from app.core.logging_config import get_logger
from app.schemas.common import PhotoModerationStatus

logger = get_logger(__name__)

class ModerationService:
    """Service for moderation operations."""

    async def get_pending_photo_moderations(self, limit: int = 50, offset: int = 0) -> tuple[List[dict], int]:
        """Get pending photo moderations."""
        results = await db.fetch_all(
            "SELECT * FROM activity.sp_get_pending_photo_moderations($1, $2)",
            limit, offset
        )

        return results, len(results)

    async def moderate_photo(self, user_id: UUID, status: PhotoModerationStatus, moderator_id: UUID) -> bool:
        """Approve or reject main photo."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_moderate_main_photo($1, $2, $3)",
            user_id, status.value, moderator_id
        )

        await cache.invalidate_user_profile(user_id)
        logger.info("photo_moderated", user_id=str(user_id), status=status.value, moderator=str(moderator_id))
        return result["success"] if result else False

    async def ban_user(self, user_id: UUID, reason: str, expires_at: Optional[datetime]) -> bool:
        """Ban user temporarily or permanently."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_ban_user($1, $2, $3)",
            user_id, reason, expires_at
        )

        await cache.invalidate_all_user_caches(user_id)
        logger.warning("user_banned", user_id=str(user_id), expires_at=str(expires_at) if expires_at else "permanent")
        return result["success"] if result else False

    async def unban_user(self, user_id: UUID) -> bool:
        """Remove ban from user."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_unban_user($1)",
            user_id
        )

        await cache.invalidate_all_user_caches(user_id)
        logger.info("user_unbanned", user_id=str(user_id))
        return result["success"] if result else False

moderation_service = ModerationService()
