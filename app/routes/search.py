"""User Search Endpoint."""
from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user, TokenPayload
from app.schemas.search import *
from app.services.search_service import SearchService, get_search_service

router = APIRouter()

@router.get("/users/search", response_model=UserSearchResponse)
async def search_users(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user: TokenPayload = Depends(get_current_user),
    service: SearchService = Depends(get_search_service)
):
    """Search users by name or username."""
    results, total = await service.search_users(q, current_user.user_id, limit, offset)
    return UserSearchResponse(results=results, total=total, limit=limit, offset=offset)