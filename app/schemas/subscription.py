"""
Pydantic schemas for subscription management endpoints.
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.schemas.common import SubscriptionLevel


class SubscriptionResponse(BaseModel):
    """Subscription details response."""
    subscription_level: SubscriptionLevel
    subscription_expires_at: Optional[datetime]
    is_captain: bool
    captain_since: Optional[datetime] = None
    days_remaining: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subscription_level": "premium",
                "subscription_expires_at": "2025-12-31T23:59:59Z",
                "is_captain": False,
                "days_remaining": 412
            }
        }
    )

    @model_validator(mode='after')
    def compute_days_remaining(self):
        if self.subscription_expires_at:
            now = datetime.now(timezone.utc)  # Use timezone-aware datetime
            if self.subscription_expires_at > now:
                 self.days_remaining = (self.subscription_expires_at - now).days
        return self


class UpdateSubscriptionRequest(BaseModel):
    """Request to update subscription (admin or payment processor only)."""
    subscription_level: SubscriptionLevel
    subscription_expires_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subscription_level": "premium",
                "subscription_expires_at": "2025-12-31T23:59:59Z"
            }
        }
    )

    @model_validator(mode='after')
    def validate_expiry(self):
        level = self.subscription_level
        v = self.subscription_expires_at

        if level == SubscriptionLevel.FREE and v is not None:
            raise ValueError("Free subscription cannot have expiry date")

        if level in [SubscriptionLevel.CLUB, SubscriptionLevel.PREMIUM] and v is None:
            raise ValueError("Club and Premium subscriptions must have expiry date")

        if v and v <= datetime.now(timezone.utc):
            raise ValueError("Expiry date must be in the future")

        return self


class UpdateSubscriptionResponse(BaseModel):
    """Response after updating subscription."""
    success: bool = True
    subscription_level: SubscriptionLevel
    subscription_expires_at: Optional[datetime]


class SetCaptainStatusRequest(BaseModel):
    """Request to grant/revoke captain status."""
    is_captain: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_captain": True
            }
        }
    )


class SetCaptainStatusResponse(BaseModel):
    """Response after setting captain status."""
    success: bool = True
    user_id: str
    is_captain: bool
    captain_since: Optional[datetime] = None
    subscription_level: SubscriptionLevel
    subscription_expires_at: Optional[datetime] = None
