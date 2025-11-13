"""Subscription Management Endpoints."""
from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_user, TokenPayload, require_admin, validate_payment_api_key
from app.schemas.subscription import *
from app.services.subscription_service import subscription_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/users/me/subscription", response_model=SubscriptionResponse)
@limiter.limit("100/minute")
async def get_subscription(current_user: TokenPayload = Depends(get_current_user)):
    """Get current subscription details."""
    data = await subscription_service.get_subscription(current_user.user_id)
    return SubscriptionResponse(**data)

@router.post("/users/me/subscription", response_model=UpdateSubscriptionResponse)
@limiter.limit("10/minute")
async def update_subscription(
    request: UpdateSubscriptionRequest,
    current_user: TokenPayload = Depends(get_current_user),
    _payment: bool = Depends(validate_payment_api_key)
):
    """Update subscription (payment processor only)."""
    await subscription_service.update_subscription(current_user.user_id, request.subscription_level, request.subscription_expires_at)
    return UpdateSubscriptionResponse(subscription_level=request.subscription_level, subscription_expires_at=request.subscription_expires_at)
