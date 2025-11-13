"""Profile Management Endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_user, TokenPayload
from app.schemas.profile import *
from app.services.profile_service import profile_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/users/me", response_model=UserProfileResponse)
@limiter.limit("100/minute")
async def get_my_profile(current_user: TokenPayload = Depends(get_current_user)):
    """Get current user's complete profile."""
    return await profile_service.get_user_profile(current_user.user_id, current_user.user_id)

@router.get("/users/{user_id}", response_model=PublicUserProfileResponse)
@limiter.limit("100/minute")
async def get_user_profile(user_id: UUID, current_user: TokenPayload = Depends(get_current_user)):
    """Get another user's public profile."""
    return await profile_service.get_public_profile(user_id, current_user.user_id, current_user.ghost_mode)

@router.patch("/users/me", response_model=UpdateProfileResponse)
@limiter.limit("20/minute")
async def update_my_profile(update_data: UpdateProfileRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Update current user's profile."""
    updated_at = await profile_service.update_profile(current_user.user_id, update_data)
    return UpdateProfileResponse(success=True, updated_at=updated_at)

@router.patch("/users/me/username", response_model=UpdateUsernameResponse)
@limiter.limit("3/hour")
async def update_username(request: UpdateUsernameRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Change username."""
    username = await profile_service.update_username(current_user.user_id, request.new_username)
    return UpdateUsernameResponse(success=True, username=username)

@router.delete("/users/me", response_model=DeleteAccountResponse)
@limiter.limit("1/hour")
async def delete_account(request: DeleteAccountRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Delete user account (soft delete)."""
    await profile_service.delete_account(current_user.user_id)
    return DeleteAccountResponse(success=True, message="Account deleted successfully")
