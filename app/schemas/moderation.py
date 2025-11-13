"""
Pydantic schemas for admin moderation endpoints.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.schemas.common import PhotoModerationStatus, UserStatus


class PendingPhotoModeration(BaseModel):
    """Single pending photo moderation entry."""
    user_id: UUID
    username: str
    email: str
    main_photo_url: str
    created_at: datetime

    class Config:
        orm_mode = True


class PendingPhotoModerationsResponse(BaseModel):
    """List of pending photo moderations."""
    results: List[PendingPhotoModeration]
    total: int
    limit: int
    offset: int

    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "username": "johndoe",
                        "email": "john@example.com",
                        "main_photo_url": "https://cdn.example.com/photos/pending123.jpg",
                        "created_at": "2024-11-13T09:00:00Z"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }


class ModeratePhotoRequest(BaseModel):
    """Request to approve or reject main photo."""
    status: PhotoModerationStatus

    @validator("status")
    def validate_status(cls, v):
        """Ensure status is approved or rejected."""
        if v not in [PhotoModerationStatus.APPROVED, PhotoModerationStatus.REJECTED]:
            raise ValueError("Status must be 'approved' or 'rejected'")
        return v

    class Config:
        schema_extra = {
            "example": {
                "status": "approved"
            }
        }


class ModeratePhotoResponse(BaseModel):
    """Response after moderating photo."""
    success: bool = True
    user_id: UUID
    moderation_status: PhotoModerationStatus


class BanUserRequest(BaseModel):
    """Request to ban user (temporary or permanent)."""
    reason: str = Field(..., max_length=1000, description="Reason for ban")
    expires_at: Optional[datetime] = Field(None, description="Ban expiry (NULL = permanent)")

    @validator("expires_at")
    def validate_expiry(cls, v):
        """Ensure expiry is in future if provided."""
        if v and v <= datetime.utcnow():
            raise ValueError("Ban expiry date must be in the future")
        return v

    class Config:
        schema_extra = {
            "example": {
                "reason": "Repeated no-shows and harassment reports",
                "expires_at": "2024-12-13T00:00:00Z"
            }
        }


class BanUserResponse(BaseModel):
    """Response after banning user."""
    success: bool = True
    user_id: UUID
    status: UserStatus
    ban_reason: str
    ban_expires_at: Optional[datetime] = None


class UnbanUserResponse(BaseModel):
    """Response after unbanning user."""
    success: bool = True
    user_id: UUID
    status: UserStatus = UserStatus.ACTIVE
