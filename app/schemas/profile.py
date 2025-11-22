"""
Pydantic schemas for profile management endpoints.
"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from app.schemas.common import InterestTag, PhotoModerationStatus, SubscriptionLevel
from app.schemas.settings import UserSettingsResponse


class UserProfileResponse(BaseModel):
    """Complete user profile response."""
    user_id: UUID
    email: EmailStr
    username: str
    first_name: str | None
    last_name: str | None
    profile_description: str | None
    main_photo_url: str | None
    main_photo_moderation_status: PhotoModerationStatus | None
    profile_photos_extra: list[str] = Field(default_factory=list)
    date_of_birth: date | None
    gender: str | None
    subscription_level: SubscriptionLevel
    subscription_expires_at: datetime | None
    is_captain: bool
    captain_since: datetime | None
    is_verified: bool
    verification_count: int
    no_show_count: int
    activities_created_count: int
    activities_attended_count: int
    created_at: datetime
    last_seen_at: datetime | None
    interests: list[InterestTag] = Field(default_factory=list)
    settings: UserSettingsResponse | None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "profile_description": "Outdoor enthusiast and coffee lover",
                "main_photo_url": "https://cdn.example.com/photos/main.jpg",
                "main_photo_moderation_status": "approved",
                "profile_photos_extra": ["https://cdn.example.com/photos/1.jpg"],
                "date_of_birth": "1990-05-15",
                "gender": "male",
                "subscription_level": "premium",
                "subscription_expires_at": "2025-12-31T23:59:59Z",
                "is_captain": False,
                "captain_since": None,
                "is_verified": True,
                "verification_count": 12,
                "no_show_count": 0,
                "activities_created_count": 8,
                "activities_attended_count": 34,
                "created_at": "2023-01-15T10:30:00Z",
                "last_seen_at": "2024-11-13T09:15:00Z",
                "interests": [
                    {"tag": "hiking", "weight": 1.0},
                    {"tag": "photography", "weight": 0.8}
                ],
                "settings": {
                    "email_notifications": True,
                    "push_notifications": True,
                    "activity_reminders": True,
                    "community_updates": True,
                    "friend_requests": True,
                    "marketing_emails": False,
                    "ghost_mode": False,
                    "language": "en",
                    "timezone": "Europe/Amsterdam"
                }
            }
        }
    )


class PublicUserProfileResponse(BaseModel):
    """Public user profile (excludes sensitive information)."""
    user_id: UUID
    username: str
    first_name: str | None
    last_name: str | None
    profile_description: str | None
    main_photo_url: str | None
    main_photo_moderation_status: PhotoModerationStatus | None
    profile_photos_extra: list[str] = Field(default_factory=list)
    gender: str | None
    is_verified: bool
    verification_count: int
    activities_created_count: int
    activities_attended_count: int
    created_at: datetime
    interests: list[InterestTag] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UpdateProfileRequest(BaseModel):
    """Request to update user profile fields."""
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    profile_description: str | None = Field(None, max_length=5000)
    date_of_birth: date | None = None
    gender: str | None = Field(None, max_length=50)
    latitude: float | None = None
    longitude: float | None = None
    postal_code: str | None = None

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, v):
        """Validate user is at least 18 years old."""
        if v:
            from datetime import date as dt_date
            today = dt_date.today()
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if age < 18:
                raise ValueError("User must be at least 18 years old")
            if v >= today:
                raise ValueError("Date of birth cannot be in the future")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "profile_description": "Updated bio text",
                "date_of_birth": "1990-05-15",
                "gender": "male",
                "latitude": 52.3676,
                "longitude": 4.9041,
                "postal_code": "1012AB"
            }
        }
    )


class UpdateProfileResponse(BaseModel):
    """Response after updating profile."""
    success: bool = True
    updated_at: datetime


class UpdateUsernameRequest(BaseModel):
    """Request to change username."""
    new_username: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]{3,30}$")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "new_username": "newusername123"
            }
        }
    )


class UpdateUsernameResponse(BaseModel):
    """Response after changing username."""
    success: bool = True
    username: str
    message: str | None = None


class DeleteAccountRequest(BaseModel):
    """Request to delete user account."""
    password: str = Field(..., description="Current password for verification")
    confirmation: str = Field(..., description="Must be exactly 'DELETE MY ACCOUNT'")

    @field_validator("confirmation")
    @classmethod
    def validate_confirmation(cls, v):
        """Ensure confirmation text matches exactly."""
        if v != "DELETE MY ACCOUNT":
            raise ValueError("Confirmation must be exactly 'DELETE MY ACCOUNT'")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "password": "current_password",
                "confirmation": "DELETE MY ACCOUNT"
            }
        }
    )


class DeleteAccountResponse(BaseModel):
    """Response after account deletion."""
    success: bool = True
    message: str = "Account deleted successfully"