"""
Profile Service - Handles all profile management business logic.
Interacts with database stored procedures and manages cache invalidation.
"""
import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.cache import cache
from app.core.database import db
from app.core.exceptions import ResourceNotFoundError, ResourceDuplicateError
from app.core.logging_config import get_logger
from app.schemas.profile import (
    PublicUserProfileResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)

logger = get_logger(__name__)


def _parse_json_fields(data: dict) -> dict:
    """
    Parse JSON string fields to actual Python objects.
    PostgreSQL JSONB columns are returned as strings by asyncpg.
    """
    json_fields = ['profile_photos_extra', 'interests', 'settings']
    for field in json_fields:
        if field in data and isinstance(data[field], str):
            try:
                data[field] = json.loads(data[field])
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, default to empty list/dict
                data[field] = [] if field != 'settings' else {}
    return data


class ProfileService:
    """
    Service for profile management operations.
    All methods interact with stored procedures and handle caching.
    """

    async def get_user_profile(
        self,
        user_id: UUID,
        requesting_user_id: UUID,
        use_cache: bool = True,
    ) -> UserProfileResponse:
        """
        Get complete user profile with interests and settings.

        Args:
            user_id: User ID to retrieve
            requesting_user_id: User making the request (for blocking checks)
            use_cache: Whether to use cached data

        Returns:
            UserProfileResponse

        Raises:
            ResourceNotFoundError: If user not found or blocked
        """
        # Try cache first (only for own profile)
        if use_cache and user_id == requesting_user_id:
            cached_profile = await cache.get_user_profile(user_id)
            if cached_profile:
                logger.debug("profile_cache_hit", user_id=str(user_id))
                return UserProfileResponse(**cached_profile)

        # Call stored procedure
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_get_user_profile($1, $2)",
            user_id,
            requesting_user_id,
        )

        if not result:
            logger.warning(
                "profile_not_found_or_blocked",
                user_id=str(user_id),
                requesting_user_id=str(requesting_user_id),
            )
            raise ResourceNotFoundError(resource="User")

        # Parse JSON fields and convert to response model
        parsed_result = _parse_json_fields(result)
        profile = UserProfileResponse(**parsed_result)

        # Cache own profile
        if user_id == requesting_user_id:
            await cache.set_user_profile(user_id, profile.dict())

        logger.info("profile_retrieved", user_id=str(user_id), requesting_user_id=str(requesting_user_id))
        return profile

    async def get_public_profile(
        self,
        user_id: UUID,
        requesting_user_id: UUID,
        ghost_mode: bool = False,
    ) -> PublicUserProfileResponse:
        """
        Get public user profile (excluding sensitive information).

        Args:
            user_id: User ID to retrieve
            requesting_user_id: User making the request
            ghost_mode: Whether requesting user has ghost mode enabled

        Returns:
            PublicUserProfileResponse

        Raises:
            ResourceNotFoundError: If user not found or blocked
        """
        # Get full profile
        full_profile = await self.get_user_profile(user_id, requesting_user_id, use_cache=True)

        # Create profile view record (only if not ghost mode)
        if not ghost_mode and user_id != requesting_user_id:
            try:
                await db.execute(
                    """
                    INSERT INTO activity.profile_views (viewer_user_id, viewed_user_id, viewed_at)
                    VALUES ($1, $2, NOW())
                    """,
                    requesting_user_id,
                    user_id,
                )
                logger.debug("profile_view_recorded", viewer=str(requesting_user_id), viewed=str(user_id))
            except Exception as e:
                logger.error("profile_view_record_failed", error=str(e))

        # Convert to public profile (exclude sensitive fields)
        public_profile = PublicUserProfileResponse(
            user_id=full_profile.user_id,
            username=full_profile.username,
            first_name=full_profile.first_name,
            last_name=full_profile.last_name,
            profile_description=full_profile.profile_description,
            main_photo_url=full_profile.main_photo_url,
            main_photo_moderation_status=full_profile.main_photo_moderation_status,
            profile_photos_extra=full_profile.profile_photos_extra,
            gender=full_profile.gender,
            is_verified=full_profile.is_verified,
            verification_count=full_profile.verification_count,
            activities_created_count=full_profile.activities_created_count,
            activities_attended_count=full_profile.activities_attended_count,
            created_at=full_profile.created_at,
            interests=full_profile.interests,
        )

        return public_profile

    async def update_profile(
        self,
        user_id: UUID,
        update_data: UpdateProfileRequest,
    ) -> datetime:
        """
        Update user profile fields.

        Args:
            user_id: User ID to update
            update_data: Profile update data

        Returns:
            Updated timestamp

        Raises:
            ResourceNotFoundError: If user not found
        """
        result = await db.fetch_one(
            """
            SELECT * FROM activity.sp_update_user_profile(
                $1, $2, $3, $4, $5, $6
            )
            """,
            user_id,
            update_data.first_name,
            update_data.last_name,
            update_data.profile_description,
            update_data.date_of_birth,
            update_data.gender,
        )

        if not result or not result["success"]:
            logger.warning("profile_update_failed", user_id=str(user_id))
            raise ResourceNotFoundError(resource="User")

        # Invalidate cache
        await cache.invalidate_user_profile(user_id)

        logger.info("profile_updated", user_id=str(user_id))
        return result["updated_at"]

    async def update_username(
        self,
        user_id: UUID,
        new_username: str,
    ) -> str:
        """
        Change username (must be unique).

        Args:
            user_id: User ID
            new_username: New username

        Returns:
            New username

        Raises:
            ResourceNotFoundError: If user not found
            ResourceDuplicateError: If username already taken
        """
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_update_username($1, $2)",
            user_id,
            new_username,
        )

        if not result["success"]:
            if "already taken" in result["message"]:
                logger.warning("username_taken", username=new_username)
                raise ResourceDuplicateError(field="username", value=new_username)
            else:
                logger.warning("username_update_failed", user_id=str(user_id))
                raise ResourceNotFoundError(resource="User")

        # Invalidate cache
        await cache.invalidate_user_profile(user_id)

        logger.info("username_updated", user_id=str(user_id), new_username=new_username)
        return new_username

    async def delete_account(
        self,
        user_id: UUID,
    ) -> bool:
        """
        Soft delete user account (GDPR compliance).

        Args:
            user_id: User ID to delete

        Returns:
            True if successful

        Raises:
            ResourceNotFoundError: If user not found
        """
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_delete_user_account($1)",
            user_id,
        )

        if not result or not result["success"]:
            logger.warning("account_deletion_failed", user_id=str(user_id))
            raise ResourceNotFoundError(resource="User")

        # Invalidate all caches
        await cache.invalidate_all_user_caches(user_id)

        logger.info("account_deleted", user_id=str(user_id))
        return True


# Global service instance
profile_service = ProfileService()
