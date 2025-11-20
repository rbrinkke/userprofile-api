"""Captain Program Endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends

from app.core.security import require_admin, TokenPayload
from app.schemas.subscription import (
    SetCaptainStatusRequest,
    SetCaptainStatusResponse,
)
from app.services.subscription_service import SubscriptionService, get_subscription_service

router = APIRouter()


@router.post("/users/{user_id}/captain", response_model=SetCaptainStatusResponse)
async def grant_captain_status(
    user_id: UUID,
    request: SetCaptainStatusRequest,
    admin: TokenPayload = Depends(require_admin),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Grant Captain status (admin only)."""
    await service.set_captain_status(user_id, request.is_captain)
    subscription = await service.get_subscription(user_id)
    return SetCaptainStatusResponse(user_id=str(user_id), **subscription.dict())


@router.delete("/users/{user_id}/captain", response_model=SetCaptainStatusResponse)
async def revoke_captain_status(
    user_id: UUID,
    admin: TokenPayload = Depends(require_admin),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Revoke Captain status (admin only)."""
    await service.set_captain_status(user_id, False)
    subscription = await service.get_subscription(user_id)
    return SetCaptainStatusResponse(user_id=str(user_id), **subscription.dict())