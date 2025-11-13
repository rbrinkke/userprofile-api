"""
Pydantic schemas for trust & verification endpoints.
"""
from pydantic import BaseModel, Field


class VerificationMetricsResponse(BaseModel):
    """User verification and trust metrics."""
    verification_count: int
    no_show_count: int
    is_verified: bool
    trust_score: float
    activities_attended_count: int

    class Config:
        schema_extra = {
            "example": {
                "verification_count": 12,
                "no_show_count": 0,
                "is_verified": True,
                "trust_score": 95.5,
                "activities_attended_count": 34
            }
        }


class IncrementVerificationResponse(BaseModel):
    """Response after incrementing verification count."""
    success: bool = True
    new_verification_count: int


class IncrementNoShowResponse(BaseModel):
    """Response after incrementing no-show count."""
    success: bool = True
    new_no_show_count: int
    warning: str = ""

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "new_no_show_count": 1,
                "warning": "User now has 1 no-show. Threshold for automatic ban is 5."
            }
        }


class UpdateActivityCountersRequest(BaseModel):
    """Request to update activity counters."""
    created_delta: int = Field(..., ge=-100, le=100, description="Change in created count")
    attended_delta: int = Field(..., ge=-100, le=100, description="Change in attended count")

    class Config:
        schema_extra = {
            "example": {
                "created_delta": 1,
                "attended_delta": 0
            }
        }


class UpdateActivityCountersResponse(BaseModel):
    """Response after updating activity counters."""
    success: bool = True
    activities_created_count: int
    activities_attended_count: int
