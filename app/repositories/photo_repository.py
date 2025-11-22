from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_db
from app.models.user import User, PhotoModerationStatus

class PhotoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_main_photo(self, user_id: UUID, photo_url: str) -> Dict[str, Any]:
        """
        Set main profile photo.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
             return {"success": False, "message": "User not found"}

        user.main_photo_url = photo_url
        user.main_photo_moderation_status = PhotoModerationStatus.pending
        user.updated_at = datetime.now()

        await self.session.commit()

        return {
            "success": True,
            "moderation_status": "pending",
            "main_photo_url": photo_url
        }

    async def add_profile_photo(self, user_id: UUID, photo_url: str) -> Dict[str, Any]:
        """
        Add photo to extra photos array.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
             return {"success": False, "message": "User not found"}

        # Initialize if None
        if user.profile_photos_extra is None:
            user.profile_photos_extra = []

        # Check limit (8)
        if len(user.profile_photos_extra) >= 8:
            return {"success": False, "message": "Maximum 8 extra photos allowed"}

        # Create a new list to ensure SQLAlchemy detects the change (for JSON types)
        new_photos = list(user.profile_photos_extra)
        if photo_url not in new_photos:
            new_photos.append(photo_url)
            user.profile_photos_extra = new_photos
            user.updated_at = datetime.now()
            await self.session.commit()
            return {"success": True, "message": "Photo added", "count": len(new_photos)}
        else:
             return {"success": False, "message": "Photo already exists"}


    async def remove_profile_photo(self, user_id: UUID, photo_url: str) -> Dict[str, Any]:
        """
        Remove photo from extra photos array.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
             return {"success": False, "message": "User not found"}

        if user.profile_photos_extra and photo_url in user.profile_photos_extra:
            new_photos = [p for p in user.profile_photos_extra if p != photo_url]
            user.profile_photos_extra = new_photos
            user.updated_at = datetime.now()
            await self.session.commit()
            return {"success": True, "message": "Photo removed", "count": len(new_photos)}

        return {"success": False, "message": "Photo not found"}

    async def get_extra_photos(self, user_id: UUID) -> List[str]:
        """
        Get extra profile photos.
        """
        query = select(User.profile_photos_extra).where(User.user_id == user_id)
        result = await self.session.execute(query)
        photos = result.scalar_one_or_none()
        return photos if photos else []

def get_photo_repository(session: AsyncSession = Depends(get_db)) -> PhotoRepository:
    return PhotoRepository(session)
