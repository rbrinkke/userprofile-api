"""User Settings Endpoints."""
from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_user, TokenPayload
from app.schemas.settings import *
from app.services.settings_service import settings_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/users/me/settings", response_model=UserSettingsResponse)
@limiter.limit("100/minute")
async def get_settings(current_user: TokenPayload = Depends(get_current_user)):
    """Get current user's settings."""
    return await settings_service.get_settings(current_user.user_id)

@router.patch("/users/me/settings", response_model=UpdateUserSettingsResponse)
@limiter.limit("20/minute")
async def update_settings(request: UpdateUserSettingsRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Update user settings (partial update)."""
    settings = await settings_service.update_settings(current_user.user_id, request)
    return UpdateUserSettingsResponse(success=True, settings=settings)
