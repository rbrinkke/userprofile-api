from typing import List, Tuple
from uuid import UUID

from fastapi import Depends
from pydantic import TypeAdapter

from app.core.database import Database, get_db
from app.schemas.search import UserSearchResult

class SearchRepository:
    search_result_adapter = TypeAdapter(List[UserSearchResult])

    def __init__(self, db: Database):
        self.db = db

    async def search_users(
        self,
        query: str,
        requesting_user_id: UUID,
        limit: int,
        offset: int
    ) -> List[UserSearchResult]:
        """
        Search users by name or username.
        """
        results = await self.db.fetch_all_raw(
            "SELECT * FROM activity.sp_search_users($1, $2, $3, $4)",
            query, requesting_user_id, limit, offset
        )
        # Convert asyncpg Record objects to dicts for Pydantic validation
        results_as_dicts = [dict(row) for row in results]
        return self.search_result_adapter.validate_python(results_as_dicts)
    async def update_last_seen(self, user_id: UUID) -> bool:
        """
        Update last seen timestamp.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_update_last_seen($1)",
            user_id
        )
        return result.get("success", False) if result else False

def get_search_repository(db: Database = Depends(get_db)) -> SearchRepository:
    return SearchRepository(db)
