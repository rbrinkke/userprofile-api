"""Interest Service - Handles interest tags management."""
from typing import List, Tuple
from uuid import UUID

from fastapi import Depends

from app.core.cache import cache
from app.core.exceptions import ResourceNotFoundError, ResourceLimitExceededError
from app.core.logging_config import get_logger
from app.repositories.interest_repository import InterestRepository, get_interest_repository
from app.schemas.common import InterestTag

logger = get_logger(__name__)

class InterestService:
    """Service for interest tags operations."""
    
    def __init__(self, interest_repo: InterestRepository):
        self.interest_repo = interest_repo

    async def get_interests(self, user_id: UUID) -> List[InterestTag]:
        """Get user interests."""
        cached = await cache.get_user_interests(user_id)
        if cached:
            return [InterestTag(**i) for i in cached]

        interests = await self.interest_repo.get_by_user_id(user_id)
        
        await cache.set_user_interests(user_id, [i.model_dump() for i in interests])
        return interests

    async def set_interests(self, user_id: UUID, interests: List[InterestTag]) -> Tuple[bool, int]:
        """Set all interests (replaces existing)."""
        response = await self.interest_repo.set_interests(user_id, interests)

        if not response.success:
            raise ResourceLimitExceededError(resource="interests", limit=20)

        await cache.invalidate_user_interests(user_id)
        await cache.invalidate_user_profile(user_id)
        logger.info("interests_set", user_id=str(user_id), count=response.interest_count)
        return response.success, response.interest_count

    async def add_interest(self, user_id: UUID, tag: str, weight: float) -> bool:
        """Add single interest."""
        response = await self.interest_repo.add_interest(user_id, tag, weight)

        if not response.success:
            message = response.message or ""
            if "Maximum" in message:
                raise ResourceLimitExceededError(resource="interests", limit=20)
            raise ResourceNotFoundError(resource="User")

        await cache.invalidate_user_interests(user_id)
        await cache.invalidate_user_profile(user_id)
        logger.info("interest_added", user_id=str(user_id), tag=tag)
        return response.success

    async def remove_interest(self, user_id: UUID, tag: str) -> bool:
        """Remove single interest."""
        response = await self.interest_repo.remove_interest(user_id, tag)

        await cache.invalidate_user_interests(user_id)
        await cache.invalidate_user_profile(user_id)
        logger.info("interest_removed", user_id=str(user_id), tag=tag)
        return response.success

def get_interest_service(repo: InterestRepository = Depends(get_interest_repository)) -> InterestService:
    """Dependency provider for InterestService."""
    return InterestService(repo)
