import json
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from app.core.database import Database
from app.schemas.profile import (
    UserProfileResponse,
    UpdateProfileRequest
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class ProfileRepository:
    def __init__(self, db: Database):
        self.db = db

    def _parse_json_fields(self, data: dict) -> dict:
        """
        Parse JSON string fields to actual Python objects.
        PostgreSQL JSONB columns are returned as strings by asyncpg.
        """
        json_fields = ['profile_photos_extra', 'interests', 'settings']
        for field in json_fields:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    data[field] = [] if field != 'settings' else {}
        return data

    async def get_by_user_id(self, user_id: UUID, requesting_user_id: UUID) -> Optional[UserProfileResponse]:
        """
        Fetch user profile from database.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_get_user_profile($1, $2)",
            user_id,
            requesting_user_id,
        )
        
        if not result:
            return None

        parsed_result = self._parse_json_fields(result)
        return UserProfileResponse(**parsed_result)

    async def record_profile_view(self, viewer_id: UUID, viewed_id: UUID) -> None:
        """
        Record that a user viewed another user's profile.
        """
        await self.db.execute(
            """
            INSERT INTO activity.profile_views (viewer_user_id, viewed_user_id, viewed_at)
            VALUES ($1, $2, NOW())
            """,
            viewer_id,
            viewed_id,
        )

    async def update(self, user_id: UUID, update_data: UpdateProfileRequest) -> Optional[datetime]:
        """
        Update user profile fields. Returns updated_at timestamp if successful.
        """
        result = await self.db.fetch_one(
            """
            SELECT * FROM activity.sp_update_user_profile(
                $1, $2, $3, $4, $5, $6
            )
            """,
            user_id,
            update_data.first_name,
            update_data.last_name,
            update_data.profile_description,
            update_data.date_of_birth,
            update_data.gender,
        )

        if result and result.get("success"):
            return result["updated_at"]
        return None

    async def update_username(self, user_id: UUID, new_username: str) -> Dict[str, Any]:
        """
        Update username. Returns dictionary with success status and message.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_update_username($1, $2)",
            user_id,
            new_username,
        )
        # The SP likely returns 'success' and 'message' columns
        return dict(result) if result else {"success": False, "message": "Database error"}

    async def delete(self, user_id: UUID) -> bool:
        """
        Soft delete user account.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_delete_user_account($1)",
            user_id,
        )
        return result is not None and result.get("success", False)