"""
Pydantic schemas for photo management endpoints.
"""
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import PhotoModerationStatus


class SetMainPhotoRequest(BaseModel):
    """Request to set main profile photo."""
    image_id: UUID = Field(..., description="Image UUID from image-api")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "image_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


class SetMainPhotoResponse(BaseModel):
    """Response after setting main photo."""
    success: bool = True
    main_photo_url: str
    moderation_status: PhotoModerationStatus
    message: str = "Photo uploaded. Awaiting moderation approval."


class AddProfilePhotoRequest(BaseModel):
    """Request to add photo to extra photos."""
    image_id: UUID = Field(..., description="Image UUID from image-api")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "image_id": "123e4567-e89b-12d3-a456-426614174001"
            }
        }
    )


class AddProfilePhotoResponse(BaseModel):
    """Response after adding photo."""
    success: bool = True
    photo_count: int
    profile_photos_extra: List[str]


class RemoveProfilePhotoRequest(BaseModel):
    """Request to remove photo from extra photos."""
    image_id: UUID = Field(..., description="Image UUID to remove")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "image_id": "123e4567-e89b-12d3-a456-426614174002"
            }
        }
    )


class RemoveProfilePhotoResponse(BaseModel):
    """Response after removing photo."""
    success: bool = True
    photo_count: int
    profile_photos_extra: List[str]