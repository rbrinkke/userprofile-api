"""Photo Management Endpoints."""
from fastapi import APIRouter

from app.dependencies import CurrentUser, PhotoSvc
from app.schemas.photos import *

router = APIRouter()

@router.post("/users/me/photos/main", response_model=SetMainPhotoResponse)
async def set_main_photo(
    request: SetMainPhotoRequest, 
    current_user: CurrentUser,
    service: PhotoSvc
):
    """Set main profile photo."""
    success, status, url = await service.set_main_photo(current_user.user_id, request.image_id)
    return SetMainPhotoResponse(success=success, main_photo_url=url, moderation_status=status)

@router.post("/users/me/photos", response_model=AddProfilePhotoResponse)
async def add_profile_photo(
    request: AddProfilePhotoRequest, 
    current_user: CurrentUser,
    service: PhotoSvc
):
    """Add photo to extra photos array."""
    success, count, photos = await service.add_profile_photo(current_user.user_id, request.image_id)
    return AddProfilePhotoResponse(success=success, photo_count=count, profile_photos_extra=photos)

@router.delete("/users/me/photos", response_model=RemoveProfilePhotoResponse)
async def remove_profile_photo(
    request: RemoveProfilePhotoRequest, 
    current_user: CurrentUser,
    service: PhotoSvc
):
    """Remove photo from extra photos array."""
    success, count, photos = await service.remove_profile_photo(current_user.user_id, request.image_id)
    return RemoveProfilePhotoResponse(success=success, photo_count=count, profile_photos_extra=photos)