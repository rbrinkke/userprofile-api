import json
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from fastapi import Depends

from app.core.database import Database, get_db
from app.schemas.profile import (
    UserProfileResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    UpdateUsernameResponse,
    DeleteAccountResponse
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class ProfileRepository:
    def __init__(self, db: Database):
        self.db = db

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

        return UserProfileResponse(**result)

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

    async def update(self, user_id: UUID, update_data: UpdateProfileRequest) -> Optional[UpdateProfileResponse]:
        """
        Update user profile fields. Returns UpdateProfileResponse if successful.
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
            return UpdateProfileResponse(
                success=True,
                updated_at=result["updated_at"]
            )
        return None

    async def update_username(self, user_id: UUID, new_username: str) -> UpdateUsernameResponse:
        """
        Update username. Returns UpdateUsernameResponse.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_update_username($1, $2)",
            user_id,
            new_username,
        )
        
        if result:
            return UpdateUsernameResponse(
                success=result.get("success", False),
                username=new_username,
                message=result.get("message")
            )
        return UpdateUsernameResponse(success=False, username=new_username, message="Database error")

    async def delete(self, user_id: UUID) -> DeleteAccountResponse:
        """
        Soft delete user account.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_delete_user_account($1)",
            user_id,
        )
        
        if result:
             return DeleteAccountResponse(
                 success=result.get("success", False),
                 message=result.get("message", "Operation completed")
             )
        return DeleteAccountResponse(success=False, message="Database error")


def get_profile_repository(db: Database = Depends(get_db)) -> ProfileRepository:
    return ProfileRepository(db)
