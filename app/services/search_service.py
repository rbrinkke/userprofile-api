"""Search Service - Handles user search and last seen."""
from typing import List
from uuid import UUID
from app.core.database import db
from app.core.exceptions import ResourceNotFoundError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class SearchService:
    """Service for user search operations."""

    async def search_users(self, query: str, requesting_user_id: UUID, limit: int = 20, offset: int = 0) -> tuple[List[dict], int]:
        """Search users by name or username."""
        results = await db.fetch_all(
            "SELECT * FROM activity.sp_search_users($1, $2, $3, $4)",
            query, requesting_user_id, limit, offset
        )

        logger.info("user_search_executed", query=query, results=len(results))
        return results, len(results)

    async def update_last_seen(self, user_id: UUID) -> bool:
        """Update last seen timestamp."""
        result = await db.fetch_one(
            "SELECT * FROM activity.sp_update_last_seen($1)",
            user_id
        )

        return result["success"] if result else False

search_service = SearchService()
