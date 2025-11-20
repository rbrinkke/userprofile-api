"""Subscription Service - Handles subscription management."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import Depends

from app.core.cache import cache
from app.core.exceptions import ResourceNotFoundError
from app.core.logging_config import get_logger
from app.repositories.subscription_repository import SubscriptionRepository, get_subscription_repository
from app.schemas.common import SubscriptionLevel
from app.schemas.subscription import SubscriptionResponse

logger = get_logger(__name__)


class SubscriptionService:
    """Service for subscription management."""

    def __init__(self, subscription_repo: SubscriptionRepository):
        self.subscription_repo = subscription_repo

    async def get_subscription(self, user_id: UUID) -> SubscriptionResponse:
        """Get current subscription details."""
        subscription = await self.subscription_repo.get(user_id)

        if not subscription:
            raise ResourceNotFoundError(resource="User")

        return subscription

    async def update_subscription(
        self,
        user_id: UUID,
        subscription_level: SubscriptionLevel,
        expires_at: Optional[datetime],
    ) -> bool:
        """Update subscription level."""
        success = await self.subscription_repo.update(
            user_id, subscription_level, expires_at
        )

        if not success:
            raise ResourceNotFoundError(resource="User")

        await cache.invalidate_all_user_caches(user_id)
        logger.info(
            "subscription_updated", user_id=str(user_id), level=subscription_level.value
        )
        return True

    async def set_captain_status(self, user_id: UUID, is_captain: bool) -> bool:
        """Grant/revoke captain status."""
        success = await self.subscription_repo.set_captain_status(user_id, is_captain)

        if not success:
            raise ResourceNotFoundError(resource="User")

        await cache.invalidate_all_user_caches(user_id)
        logger.info("captain_status_set", user_id=str(user_id), is_captain=is_captain)
        return True


def get_subscription_service(repo: SubscriptionRepository = Depends(get_subscription_repository)) -> SubscriptionService:
    """Dependency provider for SubscriptionService."""
    return SubscriptionService(repo)