import json
from typing import List, Dict, Any
from uuid import UUID

from app.core.database import Database
from app.schemas.common import InterestTag

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

    async def set_interests(self, user_id: UUID, interests: List[InterestTag]) -> Dict[str, Any]:
        """
        Set all interests (replaces existing).
        """
        interests_json = json.dumps([i.dict() for i in interests])
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_set_user_interests($1, $2::jsonb)",
            user_id, interests_json
        )
        return dict(result) if result else {"success": False, "interest_count": 0}

    async def add_interest(self, user_id: UUID, tag: str, weight: float) -> Dict[str, Any]:
        """
        Add single interest.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_add_user_interest($1, $2, $3)",
            user_id, tag, weight
        )
        return dict(result) if result else {"success": False, "message": "Database error"}

    async def remove_interest(self, user_id: UUID, tag: str) -> bool:
        """
        Remove single interest.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_remove_user_interest($1, $2)",
            user_id, tag
        )
        return result is not None and result.get("success", False)
