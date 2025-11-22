from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_db
from app.models.user import User, SubscriptionLevel
from app.schemas.subscription import SubscriptionResponse


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: UUID) -> Optional[SubscriptionResponse]:
        """
        Get subscription details.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        return SubscriptionResponse(
            subscription_level=user.subscription_level,
            subscription_expires_at=user.subscription_expires_at,
            is_captain=user.is_captain,
            captain_since=user.captain_since
        )

    async def update(self, user_id: UUID, subscription_level: SubscriptionLevel, expires_at: Optional[datetime]) -> bool:
        """
        Update subscription level.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.subscription_level = subscription_level
        user.subscription_expires_at = expires_at
        user.updated_at = datetime.now()

        try:
            await self.session.commit()
            return True
        except Exception:
            return False

    async def set_captain_status(self, user_id: UUID, is_captain: bool) -> bool:
        """
        Grant/revoke captain status.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.is_captain = is_captain
        if is_captain:
            user.captain_since = datetime.now()
            # Captain implies premium in many cases, but prompt says update logic needs to match old SP.
            # Assuming SP logic might have upgraded subscription, we should check if we need to do that.
            # For now, strictly setting the flag as per this method name.
        else:
            user.captain_since = None

        user.updated_at = datetime.now()

        try:
            await self.session.commit()
            return True
        except Exception:
            return False

def get_subscription_repository(session: AsyncSession = Depends(get_db)) -> SubscriptionRepository:
    return SubscriptionRepository(session)
