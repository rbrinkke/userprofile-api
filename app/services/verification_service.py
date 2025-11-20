"""Verification Service - Handles trust & verification."""
from typing import Dict, Tuple
from uuid import UUID

from fastapi import Depends

from app.core.cache import cache
from app.core.database import Database, get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.logging_config import get_logger
from app.repositories.verification_repository import VerificationRepository

logger = get_logger(__name__)

class VerificationService:
    """Service for verification and trust operations."""

    def __init__(self, verification_repo: VerificationRepository):
        self.verification_repo = verification_repo

    async def get_verification_metrics(self, user_id: UUID) -> dict:
        """Get verification and trust metrics."""
        result = await self.verification_repo.get_metrics(user_id)

        if not result:
            raise ResourceNotFoundError(resource="User")

        # Calculate trust score
        verification_count = result.get("verification_count", 0)
        no_show_count = result.get("no_show_count", 0)
        attended_count = result.get("activities_attended_count", 0)
        
        trust_score = min(100, (verification_count * 10) - (no_show_count * 20) + (attended_count * 0.5))
        trust_score = max(0, trust_score)

        return {
            "verification_count": verification_count,
            "no_show_count": no_show_count,
            "is_verified": result.get("is_verified", False),
            "trust_score": round(trust_score, 1),
            "activities_attended_count": attended_count
        }

    async def increment_verification(self, user_id: UUID) -> int:
        """Increment verification count."""
        result = await self.verification_repo.increment_verification(user_id)

        if not result:
             raise ResourceNotFoundError(resource="User")

        await cache.invalidate_user_profile(user_id)
        logger.info("verification_incremented", user_id=str(user_id), new_count=result.get("new_count"))
        return result.get("new_count", 0)

    async def increment_no_show(self, user_id: UUID) -> Tuple[int, str]:
        """Increment no-show count."""
        result = await self.verification_repo.increment_no_show(user_id)
        
        if not result:
             raise ResourceNotFoundError(resource="User")

        count = result.get("new_count", 0)
        warning = ""
        if count >= 5:
            warning = f"User now has {count} no-shows. Threshold for automatic ban is 5."

        await cache.invalidate_user_profile(user_id)
        logger.warning("no_show_incremented", user_id=str(user_id), new_count=count)
        return count, warning

    async def update_activity_counters(self, user_id: UUID, created_delta: int, attended_delta: int) -> Tuple[int, int]:
        """Update activity counters."""
        result = await self.verification_repo.update_activity_counters(user_id, created_delta, attended_delta)

        if not result:
             raise ResourceNotFoundError(resource="User")

        await cache.invalidate_user_profile(user_id)
        logger.info("activity_counters_updated", user_id=str(user_id))
        return result.get("new_created_count", 0), result.get("new_attended_count", 0)

def get_verification_service(db: Database = Depends(get_db)) -> VerificationService:
    """Dependency provider for VerificationService."""
    repo = VerificationRepository(db)
    return VerificationService(repo)