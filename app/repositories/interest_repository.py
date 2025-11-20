import json
from typing import List, Dict, Any
from uuid import UUID

from fastapi import Depends

from app.core.database import Database, get_db
from app.schemas.common import InterestTag
from app.schemas.interests import SetInterestsResponse, AddInterestResponse, RemoveInterestResponse

class InterestRepository:
    def __init__(self, db: Database):
        self.db = db

    async def get_by_user_id(self, user_id: UUID) -> List[InterestTag]:
        """
        Fetch user interests from database.
        """
        rows = await self.db.fetch_all(
            "SELECT interest_tag as tag, weight FROM activity.user_interests WHERE user_id = $1",
            user_id
        )
        return [InterestTag(**row) for row in rows]

    async def set_interests(self, user_id: UUID, interests: List[InterestTag]) -> SetInterestsResponse:
        """
        Set all interests (replaces existing).
        """
        interests_data = [i.model_dump() for i in interests]
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_set_user_interests($1, $2)",
            user_id, interests_data
        )
        
        if result:
            return SetInterestsResponse(
                success=result.get("success", False),
                interest_count=result.get("interest_count", 0),
                interests=interests if result.get("success") else []
            )
        return SetInterestsResponse(success=False, interest_count=0, interests=[])

    async def add_interest(self, user_id: UUID, tag: str, weight: float) -> AddInterestResponse:
        """
        Add single interest.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_add_user_interest($1, $2, $3)",
            user_id, tag, weight
        )
        
        if result:
             return AddInterestResponse(
                 success=result.get("success", False),
                 message=result.get("message", "Operation completed")
             )
        return AddInterestResponse(success=False, message="Database error")

    async def remove_interest(self, user_id: UUID, tag: str) -> RemoveInterestResponse:
        """
        Remove single interest.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_remove_user_interest($1, $2)",
            user_id, tag
        )
        
        if result:
             return RemoveInterestResponse(
                 success=result.get("success", False),
                 message=result.get("message", "Operation completed")
             )
        return RemoveInterestResponse(success=False, message="Database error")

def get_interest_repository(db: Database = Depends(get_db)) -> InterestRepository:
    return InterestRepository(db)