"""Settings Service - Handles user settings management."""
from typing import Optional
from uuid import UUID
from app.core.cache import cache
from app.core.database import db
from app.core.logging_config import get_logger
from app.schemas.settings import UpdateUserSettingsRequest, UserSettingsResponse

logger = get_logger(__name__)

class SettingsService:
    """Service for user settings operations."""

    async def get_settings(self, user_id: UUID) -> UserSettingsResponse:
        """Get user settings (creates defaults if not exists)."""
        cached = await cache.get_user_settings(user_id)
        if cached:
            return UserSettingsResponse(**cached)

        result = await db.fetch_one(
            "SELECT * FROM activity.sp_get_user_settings($1)",
            user_id
        )

        settings = UserSettingsResponse(**result)
        await cache.set_user_settings(user_id, settings.model_dump())
        return settings

    async def update_settings(self, user_id: UUID, update_data: UpdateUserSettingsRequest) -> UserSettingsResponse:
        """Update user settings."""
        result = await db.fetch_one(
            """
            SELECT * FROM activity.sp_update_user_settings(
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
            )
            """,
            user_id,
            update_data.email_notifications,
            update_data.push_notifications,
            update_data.activity_reminders,
            update_data.community_updates,
            update_data.friend_requests,
            update_data.marketing_emails,
            update_data.ghost_mode,
            update_data.language,
            update_data.timezone,
        )

        await cache.invalidate_user_settings(user_id)
        await cache.invalidate_user_profile(user_id)
        logger.info("settings_updated", user_id=str(user_id))
        return await self.get_settings(user_id)

settings_service = SettingsService()
