"""Captain Program Endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import require_admin, TokenPayload
from app.schemas.subscription import *
from app.services.subscription_service import subscription_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/users/{user_id}/captain", response_model=SetCaptainStatusResponse)
@limiter.limit("10/minute")
async def grant_captain_status(
    user_id: UUID,
    request: SetCaptainStatusRequest,
    admin: TokenPayload = Depends(require_admin)
):
    """Grant Captain status (admin only)."""
    await subscription_service.set_captain_status(user_id, request.is_captain)
    data = await subscription_service.get_subscription(user_id)
    return SetCaptainStatusResponse(user_id=str(user_id), is_captain=request.is_captain, **data)

@router.delete("/users/{user_id}/captain", response_model=SetCaptainStatusResponse)
@limiter.limit("10/minute")
async def revoke_captain_status(user_id: UUID, admin: TokenPayload = Depends(require_admin)):
    """Revoke Captain status (admin only)."""
    await subscription_service.set_captain_status(user_id, False)
    data = await subscription_service.get_subscription(user_id)
    return SetCaptainStatusResponse(user_id=str(user_id), is_captain=False, **data)
