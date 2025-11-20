"""Moderation Service - Handles admin moderation operations."""
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import Depends

from app.core.cache import cache
from app.core.database import Database, get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.logging_config import get_logger
from app.repositories.moderation_repository import ModerationRepository
from app.schemas.common import PhotoModerationStatus
from app.schemas.moderation import PendingPhotoModeration

logger = get_logger(__name__)

class ModerationService:
    """Service for moderation operations."""
    
    def __init__(self, moderation_repo: ModerationRepository):
        self.moderation_repo = moderation_repo

    async def get_pending_photo_moderations(self, limit: int = 50, offset: int = 0) -> Tuple[List[PendingPhotoModeration], int]:
        """Get pending photo moderations."""
        results = await self.moderation_repo.get_pending_photo_moderations(limit, offset)

        return results, len(results)

    async def moderate_photo(self, user_id: UUID, status: PhotoModerationStatus, moderator_id: UUID) -> bool:
        """Approve or reject main photo."""
        result = await self.moderation_repo.moderate_photo(user_id, status, moderator_id)

        await cache.invalidate_user_profile(user_id)
        logger.info("photo_moderated", user_id=str(user_id), status=status.value, moderator=str(moderator_id))
        return result.get("success", False)

    async def ban_user(self, user_id: UUID, reason: str, expires_at: Optional[datetime]) -> bool:
        """Ban user temporarily or permanently."""
        result = await self.moderation_repo.ban_user(user_id, reason, expires_at)

        await cache.invalidate_all_user_caches(user_id)
        logger.warning("user_banned", user_id=str(user_id), expires_at=str(expires_at) if expires_at else "permanent")
        return result.get("success", False)

    async def unban_user(self, user_id: UUID) -> bool:
        """Remove ban from user."""
        result = await self.moderation_repo.unban_user(user_id)

        await cache.invalidate_all_user_caches(user_id)
        logger.info("user_unbanned", user_id=str(user_id))
        return result.get("success", False)

def get_moderation_service(db: Database = Depends(get_db)) -> ModerationService:
    """Dependency provider for ModerationService."""
    repo = ModerationRepository(db)
    return ModerationService(repo)