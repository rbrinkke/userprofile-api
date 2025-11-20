"""Photo Service - Handles photo management operations."""
from typing import List, Tuple
from uuid import UUID

from fastapi import Depends

from app.config import settings
from app.core.cache import cache
from app.core.exceptions import ResourceNotFoundError, ResourceDuplicateError, ResourceLimitExceededError
from app.core.logging_config import get_logger
from app.repositories.photo_repository import PhotoRepository, get_photo_repository

logger = get_logger(__name__)

class PhotoService:
    """Service for photo management operations."""
    
    def __init__(self, photo_repo: PhotoRepository):
        self.photo_repo = photo_repo

    def _construct_photo_url(self, user_id: UUID, image_id: UUID) -> str:
        """Construct CDN URL from image ID."""
        return f"https://{settings.IMAGE_API_CDN_DOMAIN}/users/{user_id}/processed/medium/{image_id}_medium.webp"

    async def set_main_photo(self, user_id: UUID, image_id: UUID) -> Tuple[bool, str, str]:
        """Set main profile photo (triggers moderation)."""
        photo_url = self._construct_photo_url(user_id, image_id)
        result = await self.photo_repo.set_main_photo(user_id, photo_url)

        if not result.get("success"):
            raise ResourceNotFoundError(resource="User")

        await cache.invalidate_user_profile(user_id)
        logger.info("main_photo_set", user_id=str(user_id), image_id=str(image_id))
        return result.get("success"), result.get("moderation_status"), photo_url

    async def add_profile_photo(self, user_id: UUID, image_id: UUID) -> Tuple[bool, int, List[str]]:
        """Add photo to extra photos array."""
        photo_url = self._construct_photo_url(user_id, image_id)
        result = await self.photo_repo.add_profile_photo(user_id, photo_url)

        if not result.get("success"):
            message = result.get("message", "")
            if "Maximum" in message:
                raise ResourceLimitExceededError(resource="photos", limit=8)
            elif "already added" in message:
                raise ResourceDuplicateError(field="photo", value=photo_url)
            raise ResourceNotFoundError(resource="User")

        # Get updated photos
        photos = await self.photo_repo.get_extra_photos(user_id)

        await cache.invalidate_user_profile(user_id)
        logger.info("profile_photo_added", user_id=str(user_id), image_id=str(image_id), count=result.get("photo_count"))
        return result.get("success"), result.get("photo_count"), photos

    async def remove_profile_photo(self, user_id: UUID, image_id: UUID) -> Tuple[bool, int, List[str]]:
        """Remove photo from extra photos array."""
        photo_url = self._construct_photo_url(user_id, image_id)
        result = await self.photo_repo.remove_profile_photo(user_id, photo_url)

        # Get updated photos
        photos = await self.photo_repo.get_extra_photos(user_id)

        await cache.invalidate_user_profile(user_id)
        logger.info("profile_photo_removed", user_id=str(user_id), image_id=str(image_id), count=result.get("photo_count"))
        return result.get("success"), result.get("photo_count"), photos

def get_photo_service(repo: PhotoRepository = Depends(get_photo_repository)) -> PhotoService:
    """Dependency provider for PhotoService."""
    return PhotoService(repo)