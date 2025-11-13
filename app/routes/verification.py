"""Trust & Verification Endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_user, TokenPayload, validate_service_api_key
from app.schemas.verification import *
from app.services.verification_service import verification_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/users/me/verification", response_model=VerificationMetricsResponse)
@limiter.limit("100/minute")
async def get_verification_metrics(current_user: TokenPayload = Depends(get_current_user)):
    """Get verification and trust metrics."""
    data = await verification_service.get_verification_metrics(current_user.user_id)
    return VerificationMetricsResponse(**data)

@router.post("/users/{user_id}/verify", response_model=IncrementVerificationResponse)
@limiter.limit("1000/minute")
async def increment_verification(user_id: UUID, _service: str = Depends(validate_service_api_key)):
    """Increment verification count (service-to-service)."""
    count = await verification_service.increment_verification(user_id)
    return IncrementVerificationResponse(success=True, new_verification_count=count)

@router.post("/users/{user_id}/no-show", response_model=IncrementNoShowResponse)
@limiter.limit("1000/minute")
async def increment_no_show(user_id: UUID, _service: str = Depends(validate_service_api_key)):
    """Increment no-show count (service-to-service)."""
    count, warning = await verification_service.increment_no_show(user_id)
    return IncrementNoShowResponse(success=True, new_no_show_count=count, warning=warning)

@router.post("/users/{user_id}/activity-counters", response_model=UpdateActivityCountersResponse)
@limiter.limit("1000/minute")
async def update_activity_counters(
    user_id: UUID,
    request: UpdateActivityCountersRequest,
    _service: str = Depends(validate_service_api_key)
):
    """Update activity counters (service-to-service)."""
    created, attended = await verification_service.update_activity_counters(user_id, request.created_delta, request.attended_delta)
    return UpdateActivityCountersResponse(activities_created_count=created, activities_attended_count=attended)
