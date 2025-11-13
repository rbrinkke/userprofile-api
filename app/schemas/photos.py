"""
Pydantic schemas for photo management endpoints.
"""
from typing import List

from pydantic import BaseModel, Field, HttpUrl, validator

from app.schemas.common import PhotoModerationStatus


class SetMainPhotoRequest(BaseModel):
    """Request to set main profile photo."""
    photo_url: str = Field(..., max_length=500, description="Photo URL from image-api CDN")

    @validator("photo_url")
    def validate_url(cls, v):
        """Validate URL is HTTPS."""
        if not v.startswith("https://"):
            raise ValueError("Photo URL must be HTTPS")
        return v

    class Config:
        schema_extra = {
            "example": {
                "photo_url": "https://cdn.example.com/uploaded/photo123.jpg"
            }
        }


class SetMainPhotoResponse(BaseModel):
    """Response after setting main photo."""
    success: bool = True
    main_photo_url: str
    moderation_status: PhotoModerationStatus
    message: str = "Photo uploaded. Awaiting moderation approval."


class AddProfilePhotoRequest(BaseModel):
    """Request to add photo to extra photos."""
    photo_url: str = Field(..., max_length=500, description="Photo URL from image-api CDN")

    @validator("photo_url")
    def validate_url(cls, v):
        """Validate URL is HTTPS."""
        if not v.startswith("https://"):
            raise ValueError("Photo URL must be HTTPS")
        return v

    class Config:
        schema_extra = {
            "example": {
                "photo_url": "https://cdn.example.com/uploaded/photo456.jpg"
            }
        }


class AddProfilePhotoResponse(BaseModel):
    """Response after adding photo."""
    success: bool = True
    photo_count: int
    profile_photos_extra: List[str]


class RemoveProfilePhotoRequest(BaseModel):
    """Request to remove photo from extra photos."""
    photo_url: str = Field(..., max_length=500, description="Photo URL to remove")

    class Config:
        schema_extra = {
            "example": {
                "photo_url": "https://cdn.example.com/photos/1.jpg"
            }
        }


class RemoveProfilePhotoResponse(BaseModel):
    """Response after removing photo."""
    success: bool = True
    photo_count: int
    profile_photos_extra: List[str]
