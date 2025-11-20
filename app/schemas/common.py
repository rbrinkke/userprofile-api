"""
Common Pydantic schemas used across multiple endpoints.
"""
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class SubscriptionLevel(StrEnum):
    """Subscription tier enumeration."""
    FREE = "free"
    CLUB = "club"
    PREMIUM = "premium"


class PhotoModerationStatus(StrEnum):
    """Photo moderation status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UserStatus(StrEnum):
    """User account status enumeration."""
    ACTIVE = "active"
    TEMPORARY_BAN = "temporary_ban"
    BANNED = "banned"


class InterestTag(BaseModel):
    """Interest tag with weight."""
    tag: str = Field(..., min_length=1, max_length=100, description="Interest tag name")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Interest weight (0.0-1.0)")

    @field_validator("tag")
    @classmethod
    def validate_tag(cls, v):
        """Ensure tag is not just whitespace."""
        if not v.strip():
            raise ValueError("Tag cannot be empty or whitespace")
        return v.strip()


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: dict = Field(..., description="Error details")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": "User not found",
                "details": {}
            }
        }
    })