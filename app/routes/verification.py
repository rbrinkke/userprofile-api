"""Trust & Verification Endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends

from app.core.security import get_current_user, TokenPayload, validate_service_api_key
from app.schemas.verification import *
from app.services.verification_service import VerificationService, get_verification_service

router = APIRouter()

@router.get("/users/me/verification", response_model=VerificationMetricsResponse)
async def get_verification_metrics(
    current_user: TokenPayload = Depends(get_current_user),
    service: VerificationService = Depends(get_verification_service)
):
    """Get verification and trust metrics."""
    data = await service.get_verification_metrics(current_user.user_id)
    return VerificationMetricsResponse(**data)

@router.post("/users/{user_id}/verify", response_model=IncrementVerificationResponse)
async def increment_verification(
    user_id: UUID, 
    _service: str = Depends(validate_service_api_key),
    service: VerificationService = Depends(get_verification_service)
):
    """Increment verification count (service-to-service)."""
    count = await service.increment_verification(user_id)
    return IncrementVerificationResponse(success=True, new_verification_count=count)

@router.post("/users/{user_id}/no-show", response_model=IncrementNoShowResponse)
async def increment_no_show(
    user_id: UUID, 
    _service: str = Depends(validate_service_api_key),
    service: VerificationService = Depends(get_verification_service)
):
    """Increment no-show count (service-to-service)."""
    count, warning = await service.increment_no_show(user_id)
    return IncrementNoShowResponse(success=True, new_no_show_count=count, warning=warning)

@router.post("/users/{user_id}/activity-counters", response_model=UpdateActivityCountersResponse)
async def update_activity_counters(
    user_id: UUID,
    request: UpdateActivityCountersRequest,
    _service: str = Depends(validate_service_api_key),
    service: VerificationService = Depends(get_verification_service)
):
    """Update activity counters (service-to-service)."""
    created, attended = await service.update_activity_counters(user_id, request.created_delta, request.attended_delta)
    return UpdateActivityCountersResponse(activities_created_count=created, activities_attended_count=attended)