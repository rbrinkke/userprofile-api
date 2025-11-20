from typing import Optional
from uuid import UUID

from app.core.database import Database
from app.schemas.settings import UserSettingsResponse, UpdateUserSettingsRequest


class SettingsRepository:
    def __init__(self, db: Database):
        self.db = db

    async def get(self, user_id: UUID) -> Optional[UserSettingsResponse]:
        """
        Fetch user settings from database.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_get_user_settings($1)",
            user_id
        )
        if not result:
            return None
        return UserSettingsResponse(**result)

    async def update(self, user_id: UUID, update_data: UpdateUserSettingsRequest) -> bool:
        """
        Update user settings.
        """
        result = await self.db.fetch_one(
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
        return bool(result and result.get("success"))
