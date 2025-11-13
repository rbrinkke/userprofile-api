"""Last Seen Tracking Endpoint."""
from datetime import datetime
from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_user, TokenPayload
from app.schemas.search import HeartbeatResponse
from app.services.search_service import search_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/users/me/heartbeat", response_model=HeartbeatResponse)
@limiter.limit("12/hour")
async def update_heartbeat(current_user: TokenPayload = Depends(get_current_user)):
    """Update last seen timestamp."""
    await search_service.update_last_seen(current_user.user_id)
    return HeartbeatResponse(success=True, last_seen_at=datetime.utcnow().isoformat() + "Z")
