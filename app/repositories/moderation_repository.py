from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_db
from app.models.user import User, PhotoModerationStatus, UserStatus
from app.schemas.moderation import PendingPhotoModeration
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class ModerationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pending_photo_moderations(self, limit: int, offset: int) -> List[PendingPhotoModeration]:
        """
        Get pending photo moderations.
        """
        query = (
            select(User)
            .where(User.main_photo_moderation_status == PhotoModerationStatus.pending)
            .where(User.main_photo_url.is_not(None))
            .order_by(User.updated_at)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        users = result.scalars().all()

        return [
            PendingPhotoModeration(
                user_id=u.user_id,
                username=u.username,
                main_photo_url=u.main_photo_url,
                updated_at=u.updated_at
            )
            for u in users
        ]

    async def moderate_photo(self, user_id: UUID, status: PhotoModerationStatus, moderator_id: UUID) -> Dict[str, Any]:
        """
        Approve or reject main photo.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
             return {"success": False, "message": "User not found"}

        user.main_photo_moderation_status = status
        user.updated_at = datetime.now()

        # If rejected, we might want to remove the photo url or handle it differently based on requirements.
        # The SP logic for 'sp_moderate_main_photo' is not visible but typically it just sets the status.
        # If the SP did more (like notifying), that logic needs to be here or in service.

        await self.session.commit()

        return {"success": True, "message": f"Photo {status.value}"}

    async def ban_user(self, user_id: UUID, reason: str, expires_at: Optional[datetime]) -> Dict[str, Any]:
        """
        Ban user temporarily or permanently.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return {"success": False, "message": "User not found"}

        if expires_at:
            user.status = UserStatus.temporary_ban
            user.ban_expires_at = expires_at
        else:
            user.status = UserStatus.banned
            user.ban_expires_at = None

        user.ban_reason = reason
        user.updated_at = datetime.now()

        await self.session.commit()

        return {"success": True, "message": "User banned"}

    async def unban_user(self, user_id: UUID) -> Dict[str, Any]:
        """
        Remove ban from user.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return {"success": False, "message": "User not found"}

        user.status = UserStatus.active
        user.ban_expires_at = None
        user.ban_reason = None
        user.updated_at = datetime.now()

        await self.session.commit()

        return {"success": True, "message": "User unbanned"}

def get_moderation_repository(session: AsyncSession = Depends(get_db)) -> ModerationRepository:
    return ModerationRepository(session)
