"""User Settings Endpoints."""
from fastapi import APIRouter, Depends

from app.core.security import get_current_user, TokenPayload
from app.schemas.settings import (
    UpdateUserSettingsRequest,
    UpdateUserSettingsResponse,
    UserSettingsResponse,
)
from app.services.settings_service import SettingsService, get_settings_service

router = APIRouter()


@router.get("/users/me/settings", response_model=UserSettingsResponse)
async def get_settings(
    current_user: TokenPayload = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
):
    """Get current user's settings."""
    return await service.get_settings(current_user.user_id)


@router.patch("/users/me/settings", response_model=UpdateUserSettingsResponse)
async def update_settings(
    request: UpdateUserSettingsRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
):
    """Update user settings (partial update)."""
    settings = await service.update_settings(current_user.user_id, request)
    return UpdateUserSettingsResponse(success=True, settings=settings)