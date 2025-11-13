"""Photo Service - Handles photo management operations."""
from typing import List
from uuid import UUID

from app.core.cache import cache
from app.core.database import db
from app.core.exceptions import ResourceNotFoundError, ResourceDuplicateError, ResourceLimitExceededError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class PhotoService:
    """Service for photo management operations."""

    async def set_main_photo(self, user_id: UUID, photo_url: str) -> tuple[bool, str]:
        """Set main profile photo (triggers moderation)."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_set_main_photo($1, $2)",
            user_id, photo_url
        )

        if not result or not result["success"]:
            raise ResourceNotFoundError(resource="User")

        await cache.invalidate_user_profile(user_id)
        logger.info("main_photo_set", user_id=str(user_id))
        return result["success"], result["moderation_status"]

    async def add_profile_photo(self, user_id: UUID, photo_url: str) -> tuple[bool, int, List[str]]:
        """Add photo to extra photos array."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_add_profile_photo($1, $2)",
            user_id, photo_url
        )

        if not result["success"]:
            if "Maximum" in result["message"]:
                raise ResourceLimitExceededError(resource="photos", limit=8)
            elif "already added" in result["message"]:
                raise ResourceDuplicateError(field="photo", value=photo_url)
            raise ResourceNotFoundError(resource="User")

        # Get updated photos
        profile = await db.fetch_one(
            "SELECT profile_photos_extra FROM activity.users WHERE user_id = $1",
            user_id
        )

        await cache.invalidate_user_profile(user_id)
        logger.info("profile_photo_added", user_id=str(user_id), count=result["photo_count"])
        return result["success"], result["photo_count"], profile["profile_photos_extra"]

    async def remove_profile_photo(self, user_id: UUID, photo_url: str) -> tuple[bool, int, List[str]]:
        """Remove photo from extra photos array."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_remove_profile_photo($1, $2)",
            user_id, photo_url
        )

        profile = await db.fetch_one(
            "SELECT profile_photos_extra FROM activity.users WHERE user_id = $1",
            user_id
        )

        await cache.invalidate_user_profile(user_id)
        logger.info("profile_photo_removed", user_id=str(user_id), count=result["photo_count"])
        return result["success"], result["photo_count"], profile["profile_photos_extra"]

photo_service = PhotoService()
