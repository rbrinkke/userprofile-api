"""Admin Moderation Endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import require_moderator, require_admin, TokenPayload
from app.schemas.moderation import *
from app.services.moderation_service import moderation_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/admin/users/photo-moderation", response_model=PendingPhotoModerationsResponse)
@limiter.limit("100/minute")
async def get_pending_photo_moderations(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    moderator: TokenPayload = Depends(require_moderator)
):
    """Get pending main photo moderations."""
    results, total = await moderation_service.get_pending_photo_moderations(limit, offset)
    return PendingPhotoModerationsResponse(results=results, total=total, limit=limit, offset=offset)

@router.post("/admin/users/{user_id}/photo-moderation", response_model=ModeratePhotoResponse)
@limiter.limit("100/minute")
async def moderate_photo(
    user_id: UUID,
    request: ModeratePhotoRequest,
    moderator: TokenPayload = Depends(require_moderator)
):
    """Approve or reject main photo."""
    success = await moderation_service.moderate_photo(user_id, request.status, moderator.user_id)
    return ModeratePhotoResponse(success=success, user_id=user_id, moderation_status=request.status)

@router.post("/admin/users/{user_id}/ban", response_model=BanUserResponse)
@limiter.limit("10/minute")
async def ban_user(
    user_id: UUID,
    request: BanUserRequest,
    admin: TokenPayload = Depends(require_admin)
):
    """Ban user (temporary or permanent)."""
    await moderation_service.ban_user(user_id, request.reason, request.expires_at)
    status = UserStatus.TEMPORARY_BAN if request.expires_at else UserStatus.BANNED
    return BanUserResponse(user_id=user_id, status=status, ban_reason=request.reason, ban_expires_at=request.expires_at)

@router.delete("/admin/users/{user_id}/ban", response_model=UnbanUserResponse)
@limiter.limit("10/minute")
async def unban_user(user_id: UUID, admin: TokenPayload = Depends(require_admin)):
    """Remove ban from user."""
    await moderation_service.unban_user(user_id)
    return UnbanUserResponse(user_id=user_id, status=UserStatus.ACTIVE)
