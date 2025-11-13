"""Verification Service - Handles trust & verification."""
from uuid import UUID
from app.core.cache import cache
from app.core.database import db
from app.core.exceptions import ResourceNotFoundError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class VerificationService:
    """Service for verification and trust operations."""

    async def get_verification_metrics(self, user_id: UUID) -> dict:
        """Get verification and trust metrics."""
        result = await db.fetch_one(
            "SELECT verification_count, no_show_count, is_verified, activities_attended_count FROM activity.users WHERE user_id = $1",
            user_id
        )

        if not result:
            raise ResourceNotFoundError(resource="User")

        # Calculate trust score
        trust_score = min(100, (result["verification_count"] * 10) - (result["no_show_count"] * 20) + (result["activities_attended_count"] * 0.5))
        trust_score = max(0, trust_score)

        return {
            "verification_count": result["verification_count"],
            "no_show_count": result["no_show_count"],
            "is_verified": result["is_verified"],
            "trust_score": round(trust_score, 1),
            "activities_attended_count": result["activities_attended_count"]
        }

    async def increment_verification(self, user_id: UUID) -> int:
        """Increment verification count."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_increment_verification_count($1)",
            user_id
        )

        await cache.invalidate_user_profile(user_id)
        logger.info("verification_incremented", user_id=str(user_id), new_count=result["new_count"])
        return result["new_count"]

    async def increment_no_show(self, user_id: UUID) -> tuple[int, str]:
        """Increment no-show count."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_increment_no_show_count($1)",
            user_id
        )

        count = result["new_count"]
        warning = ""
        if count >= 5:
            warning = f"User now has {count} no-shows. Threshold for automatic ban is 5."

        await cache.invalidate_user_profile(user_id)
        logger.warning("no_show_incremented", user_id=str(user_id), new_count=count)
        return count, warning

    async def update_activity_counters(self, user_id: UUID, created_delta: int, attended_delta: int) -> tuple[int, int]:
        """Update activity counters."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_update_activity_counts($1, $2, $3)",
            user_id, created_delta, attended_delta
        )

        await cache.invalidate_user_profile(user_id)
        logger.info("activity_counters_updated", user_id=str(user_id))
        return result["new_created_count"], result["new_attended_count"]

verification_service = VerificationService()
