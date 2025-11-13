"""Interest Tags Endpoints."""
from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_user, TokenPayload
from app.schemas.interests import *
from app.services.interest_service import interest_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/users/me/interests", response_model=GetInterestsResponse)
@limiter.limit("100/minute")
async def get_interests(current_user: TokenPayload = Depends(get_current_user)):
    """Get current user's interests."""
    interests = await interest_service.get_interests(current_user.user_id)
    return GetInterestsResponse(interests=interests, count=len(interests))

@router.put("/users/me/interests", response_model=SetInterestsResponse)
@limiter.limit("10/minute")
async def set_interests(request: SetInterestsRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Replace all interests (bulk update)."""
    success, count = await interest_service.set_interests(current_user.user_id, request.interests)
    return SetInterestsResponse(success=success, interest_count=count, interests=request.interests)

@router.post("/users/me/interests", response_model=AddInterestResponse)
@limiter.limit("30/minute")
async def add_interest(request: AddInterestRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Add single interest."""
    await interest_service.add_interest(current_user.user_id, request.tag, request.weight)
    return AddInterestResponse(success=True, message="Interest added successfully")

@router.delete("/users/me/interests/{tag}", response_model=RemoveInterestResponse)
@limiter.limit("30/minute")
async def remove_interest(tag: str, current_user: TokenPayload = Depends(get_current_user)):
    """Remove single interest."""
    await interest_service.remove_interest(current_user.user_id, tag)
    return RemoveInterestResponse(success=True, message="Interest removed successfully")
