from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, update, delete, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User, UserStatus
from app.models.settings import UserSettings
from app.models.interests import UserInterests
from app.models.blocking import UserBlock
from app.models.profile_view import ProfileView
from app.schemas.profile import (
    UserProfileResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    UpdateUsernameResponse,
    DeleteAccountResponse
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: UUID, requesting_user_id: UUID) -> Optional[UserProfileResponse]:
        """
        Fetch user profile from database with asymmetric blocking logic.
        """
        # Check for blocking
        block_query = select(UserBlock).where(
            or_(
                (UserBlock.blocker_user_id == user_id) & (UserBlock.blocked_user_id == requesting_user_id),
                (UserBlock.blocker_user_id == requesting_user_id) & (UserBlock.blocked_user_id == user_id)
            )
        )
        block_result = await self.session.execute(block_query)
        if block_result.first():
            # If there is a block, return None or handle appropriately (e.g. raise exception)
            # Based on old SP logic, it likely returns empty/null, effectively "user not found"
            return None

        # Fetch user with related data
        query = (
            select(User)
            .options(selectinload(User.settings), selectinload(User.interests))
            .where(User.user_id == user_id)
        )
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Transform to response schema
        # We need to construct the response carefully to match UserProfileResponse
        # Assuming UserProfileResponse structure, we might need to adapt.
        # Since I don't have the exact definition of UserProfileResponse, I'll map fields.

        # Map interests
        # UserProfileResponse expects List[InterestTag], which has 'tag' and 'weight'
        interests_list = [
            {"tag": i.interest_tag, "weight": i.weight}
            for i in user.interests
        ] if user.interests else []

        # Map settings
        settings_dict = user.settings.model_dump() if user.settings else None

        # Construct response
        user_dict = user.model_dump()
        user_dict['interests'] = interests_list
        user_dict['settings'] = settings_dict

        # Handle any other fields that might differ (e.g. aggregated counts if not in User model)
        # For now assuming User model has all necessary fields or they are mapped.

        return UserProfileResponse(**user_dict)

    async def record_profile_view(self, viewer_id: UUID, viewed_id: UUID) -> None:
        """
        Record that a user viewed another user's profile.
        """
        if viewer_id == viewed_id:
            return

        # Check ghost mode
        settings_query = select(UserSettings).where(UserSettings.user_id == viewer_id)
        settings_result = await self.session.execute(settings_query)
        settings = settings_result.scalar_one_or_none()

        if settings and settings.ghost_mode:
            return

        view = ProfileView(viewer_user_id=viewer_id, viewed_user_id=viewed_id)
        self.session.add(view)
        # We might want to commit here or let the service layer handle it.
        # Usually repositories don't commit unless it's a self-contained action.
        # But the original code did execute immediately. I will commit here for consistency with previous behavior.
        await self.session.commit()

    async def update(self, user_id: UUID, update_data: UpdateProfileRequest) -> Optional[UpdateProfileResponse]:
        """
        Update user profile fields. Returns UpdateProfileResponse if successful.
        """
        # Get user
        user_query = select(User).where(User.user_id == user_id)
        user_result = await self.session.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return None

        # Update fields
        if update_data.first_name is not None:
            user.first_name = update_data.first_name
        if update_data.last_name is not None:
            user.last_name = update_data.last_name
        if update_data.profile_description is not None:
            user.profile_description = update_data.profile_description
        if update_data.date_of_birth is not None:
            # Validate age 18+ (logic moved from SP)
            today = datetime.now().date()
            age = today.year - update_data.date_of_birth.year - ((today.month, today.day) < (update_data.date_of_birth.month, update_data.date_of_birth.day))
            if age < 18:
                # In a real app, maybe raise a specific exception
                logger.warning(f"Update rejected: User {user_id} is underage ({age})")
                return None # Or raise exception
            if update_data.date_of_birth > today:
                logger.warning(f"Update rejected: Date of birth in future")
                return None
            user.date_of_birth = update_data.date_of_birth
        if update_data.gender is not None:
            user.gender = update_data.gender

        user.updated_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(user)

        return UpdateProfileResponse(
            success=True,
            updated_at=user.updated_at
        )

    async def update_username(self, user_id: UUID, new_username: str) -> UpdateUsernameResponse:
        """
        Update username. Returns UpdateUsernameResponse.
        """
        # Check uniqueness
        query = select(User).where(func.lower(User.username) == new_username.lower())
        result = await self.session.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
             return UpdateUsernameResponse(
                success=False,
                username=new_username,
                message="Username already taken"
            )

        user_query = select(User).where(User.user_id == user_id)
        user_result = await self.session.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
             return UpdateUsernameResponse(
                success=False,
                username=new_username,
                message="User not found"
            )

        user.username = new_username
        user.updated_at = datetime.now()
        await self.session.commit()

        return UpdateUsernameResponse(
            success=True,
            username=new_username,
            message="Username updated successfully"
        )

    async def delete(self, user_id: UUID) -> DeleteAccountResponse:
        """
        Soft delete user account.
        """
        user_query = select(User).where(User.user_id == user_id)
        user_result = await self.session.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return DeleteAccountResponse(success=False, message="User not found")

        # Perform soft delete
        # SET status='banned', email='deleted_...', ...
        timestamp = datetime.now().timestamp()
        user.status = UserStatus.banned
        user.email = f"deleted_{timestamp}_{user.email}"
        user.username = f"deleted_{timestamp}_{user.username}"
        user.updated_at = datetime.now()

        # Delete related data
        # Note: Cascade delete in DB might handle some, but strictly following prompt "subsequent DELETE operations"
        # Actually the schema has ON DELETE CASCADE for most things referencing users.
        # BUT the prompt says "perform ... subsequent DELETE operations on related tables (user_interests, user_settings)"
        # Since we are doing soft delete on User, the CASCADE won't trigger unless we actually DELETE the user row.
        # But we are UPDATING the user row to banned/deleted.
        # So we must manually delete related rows if that is the desired behavior for "soft delete".
        
        # Delete interests
        await self.session.execute(delete(UserInterests).where(UserInterests.user_id == user_id))

        # Delete settings (or maybe we should keep them? Prompt says delete)
        await self.session.execute(delete(UserSettings).where(UserSettings.user_id == user_id))

        # Logic from SP 23 likely cleared these.

        await self.session.commit()

        return DeleteAccountResponse(
             success=True,
             message="Account deleted successfully"
         )


def get_profile_repository(session: AsyncSession = Depends(get_db)) -> ProfileRepository:
    return ProfileRepository(session)
