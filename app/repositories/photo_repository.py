import json
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import Depends

from app.core.database import Database, get_db

class PhotoRepository:
    def __init__(self, db: Database):
        self.db = db

    async def set_main_photo(self, user_id: UUID, photo_url: str) -> Dict[str, Any]:
        """
        Set main profile photo.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_set_main_photo($1, $2)",
            user_id, photo_url
        )
        return dict(result) if result else {"success": False, "moderation_status": "PENDING"}

    async def add_profile_photo(self, user_id: UUID, photo_url: str) -> Dict[str, Any]:
        """
        Add photo to extra photos array.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_add_profile_photo($1, $2)",
            user_id, photo_url
        )
        return dict(result) if result else {"success": False, "message": "Database error"}

    async def remove_profile_photo(self, user_id: UUID, photo_url: str) -> Dict[str, Any]:
        """
        Remove photo from extra photos array.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_remove_profile_photo($1, $2)",
            user_id, photo_url
        )
        return dict(result) if result else {"success": False, "interest_count": 0}

    async def get_extra_photos(self, user_id: UUID) -> List[str]:
        """
        Get extra profile photos.
        """
        result = await self.db.fetch_one(
            "SELECT profile_photos_extra FROM activity.users WHERE user_id = $1",
            user_id
        )
        if result:
            return result.get("profile_photos_extra") or []
        return []

def get_photo_repository(db: Database = Depends(get_db)) -> PhotoRepository:
    return PhotoRepository(db)