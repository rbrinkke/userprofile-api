"""
Pydantic schemas for interest tags endpoints.
"""
from typing import List

from pydantic import BaseModel, Field, validator

from app.schemas.common import InterestTag, SuccessResponse


class GetInterestsResponse(BaseModel):
    """Response with user interests."""
    interests: List[InterestTag] = Field(default_factory=list)
    count: int

    class Config:
        schema_extra = {
            "example": {
                "interests": [
                    {"tag": "hiking", "weight": 1.0},
                    {"tag": "photography", "weight": 0.8},
                    {"tag": "coffee", "weight": 0.6}
                ],
                "count": 3
            }
        }


class SetInterestsRequest(BaseModel):
    """Request to replace all interests (bulk update)."""
    interests: List[InterestTag] = Field(..., max_items=20, description="List of interests (max 20)")

    @validator("interests")
    def validate_unique_tags(cls, v):
        """Ensure tags are unique."""
        tags = [interest.tag.lower() for interest in v]
        if len(tags) != len(set(tags)):
            raise ValueError("Interest tags must be unique")
        return v

    class Config:
        schema_extra = {
            "example": {
                "interests": [
                    {"tag": "hiking", "weight": 1.0},
                    {"tag": "photography", "weight": 0.8},
                    {"tag": "coffee", "weight": 0.6}
                ]
            }
        }


class SetInterestsResponse(BaseModel):
    """Response after setting interests."""
    success: bool = True
    interest_count: int
    interests: List[InterestTag]


class AddInterestRequest(BaseModel):
    """Request to add single interest."""
    tag: str = Field(..., min_length=1, max_length=100, description="Interest tag name")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Interest weight (0.0-1.0)")

    @validator("tag")
    def validate_tag(cls, v):
        """Ensure tag is not just whitespace."""
        if not v.strip():
            raise ValueError("Tag cannot be empty or whitespace")
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "tag": "running",
                "weight": 0.9
            }
        }


class AddInterestResponse(SuccessResponse):
    """Response after adding interest."""
    message: str = "Interest added successfully"


class RemoveInterestResponse(SuccessResponse):
    """Response after removing interest."""
    message: str = "Interest removed successfully"
