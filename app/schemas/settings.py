"""
Pydantic schemas for user settings endpoints.
"""
from typing import Optional

from pydantic import BaseModel, Field, validator


class UserSettingsResponse(BaseModel):
    """User settings response."""
    email_notifications: bool
    push_notifications: bool
    activity_reminders: bool
    community_updates: bool
    friend_requests: bool
    marketing_emails: bool
    ghost_mode: bool
    language: str
    timezone: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
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


class UpdateUserSettingsRequest(BaseModel):
    """Request to update user settings (partial update)."""
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    activity_reminders: Optional[bool] = None
    community_updates: Optional[bool] = None
    friend_requests: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    ghost_mode: Optional[bool] = None
    language: Optional[str] = Field(None, min_length=2, max_length=10, description="ISO 639-1 language code")
    timezone: Optional[str] = Field(None, max_length=50, description="IANA timezone string")

    @validator("language")
    def validate_language(cls, v):
        """Validate language code format."""
        if v and len(v) not in [2, 5]:  # en or en-US
            raise ValueError("Language must be 2 or 5 character ISO 639-1 code")
        return v

    class Config:
        schema_extra = {
            "example": {
                "email_notifications": False,
                "push_notifications": True,
                "ghost_mode": True,
                "language": "nl",
                "timezone": "Europe/Berlin"
            }
        }


class UpdateUserSettingsResponse(BaseModel):
    """Response after updating settings."""
    success: bool = True
    settings: UserSettingsResponse
