"""User Settings Endpoints."""
from fastapi import APIRouter, Depends

from app.core.security import get_current_user, TokenPayload
from app.schemas.settings import *
from app.services.settings_service import settings_service

router = APIRouter()

@router.get("/users/me/settings", response_model=UserSettingsResponse)
async def get_settings(current_user: TokenPayload = Depends(get_current_user)):
    """Get current user's settings."""
    return await settings_service.get_settings(current_user.user_id)

@router.patch("/users/me/settings", response_model=UpdateUserSettingsResponse)
async def update_settings(request: UpdateUserSettingsRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Update user settings (partial update)."""
    settings = await settings_service.update_settings(current_user.user_id, request)
    return UpdateUserSettingsResponse(success=True, settings=settings)
