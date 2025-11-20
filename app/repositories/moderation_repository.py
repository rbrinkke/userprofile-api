from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.core.database import Database
from app.schemas.common import PhotoModerationStatus
from app.schemas.moderation import PendingPhotoModeration

class ModerationRepository:
    def __init__(self, db: Database):
        self.db = db

    async def get_pending_photo_moderations(self, limit: int, offset: int) -> List[PendingPhotoModeration]:
        """
        Get pending photo moderations.
        """
        results = await self.db.fetch_all(
            "SELECT * FROM activity.sp_get_pending_photo_moderations($1, $2)",
            limit, offset
        )
        return [PendingPhotoModeration(**row) for row in results]

    async def moderate_photo(self, user_id: UUID, status: PhotoModerationStatus, moderator_id: UUID) -> Dict[str, Any]:
        """
        Approve or reject main photo.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_moderate_main_photo($1, $2, $3)",
            user_id, status.value, moderator_id
        )
        return dict(result) if result else {}

    async def ban_user(self, user_id: UUID, reason: str, expires_at: Optional[datetime]) -> Dict[str, Any]:
        """
        Ban user temporarily or permanently.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_ban_user($1, $2, $3)",
            user_id, reason, expires_at
        )
        return dict(result) if result else {}

    async def unban_user(self, user_id: UUID) -> Dict[str, Any]:
        """
        Remove ban from user.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_unban_user($1)",
            user_id
        )
        return dict(result) if result else {}
