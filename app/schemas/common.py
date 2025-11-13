"""
Common Pydantic schemas used across multiple endpoints.
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class SubscriptionLevel(str, Enum):
    """Subscription tier enumeration."""
    FREE = "free"
    CLUB = "club"
    PREMIUM = "premium"


class PhotoModerationStatus(str, Enum):
    """Photo moderation status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UserStatus(str, Enum):
    """User account status enumeration."""
    ACTIVE = "active"
    TEMPORARY_BAN = "temporary_ban"
    BANNED = "banned"


class InterestTag(BaseModel):
    """Interest tag with weight."""
    tag: str = Field(..., min_length=1, max_length=100, description="Interest tag name")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Interest weight (0.0-1.0)")

    @validator("tag")
    def validate_tag(cls, v):
        """Ensure tag is not just whitespace."""
        if not v.strip():
            raise ValueError("Tag cannot be empty or whitespace")
        return v.strip()


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: dict = Field(..., description="Error details")

    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": "User not found",
                    "details": {}
                }
            }
        }
