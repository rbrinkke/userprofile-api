"""Photo Management Endpoints."""
from fastapi import APIRouter, Depends

from app.core.security import get_current_user, TokenPayload
from app.schemas.photos import *
from app.services.photo_service import photo_service

router = APIRouter()

@router.post("/users/me/photos/main", response_model=SetMainPhotoResponse)
async def set_main_photo(request: SetMainPhotoRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Set main profile photo."""
    success, status = await photo_service.set_main_photo(current_user.user_id, request.photo_url)
    return SetMainPhotoResponse(success=success, main_photo_url=request.photo_url, moderation_status=status)

@router.post("/users/me/photos", response_model=AddProfilePhotoResponse)
async def add_profile_photo(request: AddProfilePhotoRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Add photo to extra photos array."""
    success, count, photos = await photo_service.add_profile_photo(current_user.user_id, request.photo_url)
    return AddProfilePhotoResponse(success=success, photo_count=count, profile_photos_extra=photos)

@router.delete("/users/me/photos", response_model=RemoveProfilePhotoResponse)
async def remove_profile_photo(request: RemoveProfilePhotoRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Remove photo from extra photos array."""
    success, count, photos = await photo_service.remove_profile_photo(current_user.user_id, request.photo_url)
    return RemoveProfilePhotoResponse(success=success, photo_count=count, profile_photos_extra=photos)
