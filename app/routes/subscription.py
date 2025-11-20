"""Subscription Management Endpoints."""
from fastapi import APIRouter, Depends

from app.core.security import get_current_user, TokenPayload, validate_payment_api_key
from app.schemas.subscription import (
    SubscriptionResponse,
    UpdateSubscriptionRequest,
    UpdateSubscriptionResponse,
)
from app.services.subscription_service import SubscriptionService, get_subscription_service

router = APIRouter()


@router.get("/users/me/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: TokenPayload = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Get current subscription details."""
    return await service.get_subscription(current_user.user_id)


@router.post("/users/me/subscription", response_model=UpdateSubscriptionResponse)
async def update_subscription(
    request: UpdateSubscriptionRequest,
    current_user: TokenPayload = Depends(get_current_user),
    _payment: bool = Depends(validate_payment_api_key),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Update subscription (payment processor only)."""
    await service.update_subscription(
        current_user.user_id, request.subscription_level, request.subscription_expires_at
    )
    return UpdateSubscriptionResponse(
        subscription_level=request.subscription_level,
        subscription_expires_at=request.subscription_expires_at,
    )