"""Profile Management Endpoints."""
from uuid import UUID
from fastapi import APIRouter

from app.dependencies import CurrentUser, ProfileSvc
from app.schemas.profile import (
    DeleteAccountRequest,
    DeleteAccountResponse,
    PublicUserProfileResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    UpdateUsernameRequest,
    UpdateUsernameResponse,
    UserProfileResponse,
)

router = APIRouter()


@router.get("/users/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: CurrentUser,
    service: ProfileSvc,
):
    """Get current user's complete profile."""
    return await service.get_user_profile(current_user.user_id, current_user.user_id)


@router.get("/users/{user_id}", response_model=PublicUserProfileResponse)
async def get_user_profile(
    user_id: UUID,
    current_user: CurrentUser,
    service: ProfileSvc,
):
    """Get another user's public profile."""
    return await service.get_public_profile(
        user_id, current_user.user_id, current_user.ghost_mode
    )


@router.patch("/users/me", response_model=UpdateProfileResponse)
async def update_my_profile(
    update_data: UpdateProfileRequest,
    current_user: CurrentUser,
    service: ProfileSvc,
):
    """Update current user's profile."""
    updated_at = await service.update_profile(current_user.user_id, update_data)
    return UpdateProfileResponse(success=True, updated_at=updated_at)


@router.patch("/users/me/username", response_model=UpdateUsernameResponse)
async def update_username(
    request: UpdateUsernameRequest,
    current_user: CurrentUser,
    service: ProfileSvc,
):
    """Change username."""
    username = await service.update_username(
        current_user.user_id, request.new_username
    )
    return UpdateUsernameResponse(success=True, username=username)


@router.delete("/users/me", response_model=DeleteAccountResponse)
async def delete_account(
    request: DeleteAccountRequest,
    current_user: CurrentUser,
    service: ProfileSvc,
):
    """Delete user account (soft delete)."""
    await service.delete_account(current_user.user_id)
    return DeleteAccountResponse(success=True, message="Account deleted successfully")