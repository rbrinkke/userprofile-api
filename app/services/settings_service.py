"""Settings Service - Handles user settings management."""
from typing import Optional
from uuid import UUID

from fastapi import Depends

from app.core.cache import cache
from app.core.database import Database, get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.logging_config import get_logger
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import UpdateUserSettingsRequest, UserSettingsResponse

logger = get_logger(__name__)


class SettingsService:
    """Service for user settings operations."""

    def __init__(self, settings_repo: SettingsRepository):
        self.settings_repo = settings_repo

    async def get_settings(self, user_id: UUID) -> UserSettingsResponse:
        """Get user settings (creates defaults if not exists)."""
        cached = await cache.get_user_settings(user_id)
        if cached:
            return UserSettingsResponse(**cached)

        settings = await self.settings_repo.get(user_id)
        
        if not settings:
            # In case the SP doesn't create defaults or returns nothing
            raise ResourceNotFoundError(resource="Settings")

        await cache.set_user_settings(user_id, settings.model_dump())
        return settings

    async def update_settings(self, user_id: UUID, update_data: UpdateUserSettingsRequest) -> UserSettingsResponse:
        """Update user settings."""
        success = await self.settings_repo.update(user_id, update_data)
        
        if not success:
             # Could happen if user doesn't exist or DB error
             logger.warning("settings_update_failed", user_id=str(user_id))
             # We proceed to get_settings which might fail if user missing, or return old settings

        await cache.invalidate_user_settings(user_id)
        await cache.invalidate_user_profile(user_id)
        logger.info("settings_updated", user_id=str(user_id))
        return await self.get_settings(user_id)


def get_settings_service(db: Database = Depends(get_db)) -> SettingsService:
    """Dependency provider for SettingsService."""
    repo = SettingsRepository(db)
    return SettingsService(repo)