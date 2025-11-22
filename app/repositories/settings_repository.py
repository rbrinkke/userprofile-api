from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_db
from app.models.settings import UserSettings
from app.schemas.settings import UserSettingsResponse, UpdateUserSettingsRequest


class SettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: UUID) -> Optional[UserSettingsResponse]:
        """
        Fetch user settings from database.
        """
        query = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.session.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            # In SP logic, it might return default settings if not found, or just None.
            # Assuming we want to return None if strictly not found, or creating default if expected.
            # The SP `sp_get_user_settings` might have created default settings on the fly.
            # For now, returning None.
            return None

        return UserSettingsResponse(**settings.model_dump())

    async def update(self, user_id: UUID, update_data: UpdateUserSettingsRequest) -> bool:
        """
        Update user settings.
        """
        query = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.session.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            # If settings don't exist, create them
            settings = UserSettings(user_id=user_id)
            self.session.add(settings)

        # Update fields
        if update_data.email_notifications is not None:
            settings.email_notifications = update_data.email_notifications
        if update_data.push_notifications is not None:
            settings.push_notifications = update_data.push_notifications
        if update_data.activity_reminders is not None:
            settings.activity_reminders = update_data.activity_reminders
        if update_data.community_updates is not None:
            settings.community_updates = update_data.community_updates
        if update_data.friend_requests is not None:
            settings.friend_requests = update_data.friend_requests
        if update_data.marketing_emails is not None:
            settings.marketing_emails = update_data.marketing_emails
        if update_data.ghost_mode is not None:
            settings.ghost_mode = update_data.ghost_mode
        if update_data.language is not None:
            settings.language = update_data.language
        if update_data.timezone is not None:
            settings.timezone = update_data.timezone

        settings.updated_at = datetime.now()

        try:
            await self.session.commit()
            return True
        except Exception:
            return False

def get_settings_repository(session: AsyncSession = Depends(get_db)) -> SettingsRepository:
    return SettingsRepository(session)
