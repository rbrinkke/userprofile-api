"""
Pydantic schemas for user search endpoints.
"""
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserSearchResult(BaseModel):
    """Single user search result."""
    user_id: UUID
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    main_photo_url: Optional[str]
    is_verified: bool
    verification_count: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "main_photo_url": "https://cdn.example.com/photos/john.jpg",
                "is_verified": True,
                "verification_count": 12
            }
        }


class UserSearchResponse(BaseModel):
    """User search results with pagination."""
    results: List[UserSearchResult]
    total: int
    limit: int
    offset: int

    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "username": "johndoe",
                        "first_name": "John",
                        "last_name": "Doe",
                        "main_photo_url": "https://cdn.example.com/photos/john.jpg",
                        "is_verified": True,
                        "verification_count": 12
                    }
                ],
                "total": 1,
                "limit": 20,
                "offset": 0
            }
        }


class HeartbeatResponse(BaseModel):
    """Response after updating last seen timestamp."""
    success: bool = True
    last_seen_at: str

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "last_seen_at": "2024-11-13T10:45:00Z"
            }
        }
