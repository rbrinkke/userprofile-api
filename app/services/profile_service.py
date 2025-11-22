"""
Profile Service - Handles all profile management business logic.
Interacts with ProfileRepository and manages cache invalidation.
"""
from datetime import datetime
from uuid import UUID

from fastapi import Depends

from app.core.cache import cache
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError, ResourceDuplicateError
from app.core.logging_config import get_logger
from app.repositories.profile_repository import ProfileRepository, get_profile_repository
from app.schemas.profile import (
    PublicUserProfileResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)

logger = get_logger(__name__)


class ProfileService:
    """
    Service for profile management operations.
    All methods interact with ProfileRepository and handle caching.
    """

    def __init__(self, profile_repo: ProfileRepository):
        self.profile_repo = profile_repo

    async def get_user_profile(
        self,
        user_id: UUID,
        requesting_user_id: UUID,
        use_cache: bool = True,
    ) -> UserProfileResponse:
        """
        Get complete user profile with interests and settings.
        """
        # Try cache first (only for own profile)
        if use_cache and user_id == requesting_user_id:
            cached_profile = await cache.get_user_profile(user_id)
            if cached_profile:
                logger.debug("profile_cache_hit", user_id=str(user_id))
                return UserProfileResponse(**cached_profile)

        # Call repository
        profile = await self.profile_repo.get_by_user_id(user_id, requesting_user_id)

        if not profile:
            logger.warning(
                "profile_not_found_or_blocked",
                user_id=str(user_id),
                requesting_user_id=str(requesting_user_id),
            )
            raise ResourceNotFoundError(resource="User")

        # Cache own profile
        if user_id == requesting_user_id:
            await cache.set_user_profile(user_id, profile.model_dump())

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
        """
        # Get full profile
        full_profile = await self.get_user_profile(user_id, requesting_user_id, use_cache=True)

        # Create profile view record (only if not ghost mode)
        if not ghost_mode and user_id != requesting_user_id:
            try:
                await self.profile_repo.record_profile_view(requesting_user_id, user_id)
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
        """
        response = await self.profile_repo.update(user_id, update_data)

        if not response:
            logger.warning("profile_update_failed", user_id=str(user_id))
            raise ResourceNotFoundError(resource="User")

        # Invalidate cache
        await cache.invalidate_user_profile(user_id)

        logger.info("profile_updated", user_id=str(user_id))
        return response.updated_at

    async def update_username(
        self,
        user_id: UUID,
        new_username: str,
    ) -> str:
        """
        Change username (must be unique).
        """
        result = await self.profile_repo.update_username(user_id, new_username)

        if not result.success:
            if result.message and "already taken" in result.message:
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
        """
        response = await self.profile_repo.delete(user_id)

        if not response.success:
            logger.warning("account_deletion_failed", user_id=str(user_id))
            raise ResourceNotFoundError(resource="User")

        # Invalidate all caches
        await cache.invalidate_all_user_caches(user_id)

        logger.info("account_deleted", user_id=str(user_id))
        return True


def get_profile_service(repo: ProfileRepository = Depends(get_profile_repository)) -> ProfileService:
    """
    Dependency provider for ProfileService.
    """
    return ProfileService(repo)
