"""
Pydantic schemas for subscription management endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator

from app.schemas.common import SubscriptionLevel


class SubscriptionResponse(BaseModel):
    """Subscription details response."""
    subscription_level: SubscriptionLevel
    subscription_expires_at: Optional[datetime]
    is_captain: bool
    days_remaining: Optional[int] = None

    @validator("days_remaining", always=True)
    def calculate_days_remaining(cls, v, values):
        """Calculate days remaining until subscription expires."""
        if values.get("subscription_expires_at"):
            expires_at = values["subscription_expires_at"]
            now = datetime.utcnow()
            if expires_at > now:
                return (expires_at - now).days
        return None

    class Config:
        schema_extra = {
            "example": {
                "subscription_level": "premium",
                "subscription_expires_at": "2025-12-31T23:59:59Z",
                "is_captain": False,
                "days_remaining": 412
            }
        }


class UpdateSubscriptionRequest(BaseModel):
    """Request to update subscription (admin or payment processor only)."""
    subscription_level: SubscriptionLevel
    subscription_expires_at: Optional[datetime] = None

    @validator("subscription_expires_at", always=True)
    def validate_expiry(cls, v, values):
        """Validate expiry based on subscription level."""
        level = values.get("subscription_level")

        if level == SubscriptionLevel.FREE and v is not None:
            raise ValueError("Free subscription cannot have expiry date")

        if level in [SubscriptionLevel.CLUB, SubscriptionLevel.PREMIUM] and v is None:
            raise ValueError("Club and Premium subscriptions must have expiry date")

        if v and v <= datetime.utcnow():
            raise ValueError("Expiry date must be in the future")

        return v

    class Config:
        schema_extra = {
            "example": {
                "subscription_level": "premium",
                "subscription_expires_at": "2025-12-31T23:59:59Z"
            }
        }


class UpdateSubscriptionResponse(BaseModel):
    """Response after updating subscription."""
    success: bool = True
    subscription_level: SubscriptionLevel
    subscription_expires_at: Optional[datetime]


class SetCaptainStatusRequest(BaseModel):
    """Request to grant/revoke captain status."""
    is_captain: bool

    class Config:
        schema_extra = {
            "example": {
                "is_captain": True
            }
        }


class SetCaptainStatusResponse(BaseModel):
    """Response after setting captain status."""
    success: bool = True
    user_id: str
    is_captain: bool
    captain_since: Optional[datetime] = None
    subscription_level: SubscriptionLevel
    subscription_expires_at: Optional[datetime] = None
