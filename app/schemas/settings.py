"""
Pydantic schemas for user settings endpoints.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict


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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
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
    )


class UpdateUserSettingsRequest(BaseModel):
    """Request to update user settings (partial update)."""
    email_notifications: bool | None = None
    push_notifications: bool | None = None
    activity_reminders: bool | None = None
    community_updates: bool | None = None
    friend_requests: bool | None = None
    marketing_emails: bool | None = None
    ghost_mode: bool | None = None
    language: str | None = Field(None, min_length=2, max_length=10, description="ISO 639-1 language code")
    timezone: str | None = Field(None, max_length=50, description="IANA timezone string")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        """Validate language code format."""
        if v and len(v) not in [2, 5]:  # en or en-US
            raise ValueError("Language must be 2 or 5 character ISO 639-1 code")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_notifications": False,
                "push_notifications": True,
                "ghost_mode": True,
                "language": "nl",
                "timezone": "Europe/Berlin"
            }
        }
    )


class UpdateUserSettingsResponse(BaseModel):
    """Response after updating settings."""
    success: bool = True
    settings: UserSettingsResponse