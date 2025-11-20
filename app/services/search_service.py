"""Search Service - Handles user search and last seen."""
from typing import List, Tuple
from uuid import UUID

from fastapi import Depends

from app.core.database import Database
from app.core.exceptions import ResourceNotFoundError
from app.core.logging_config import get_logger
from app.repositories.search_repository import SearchRepository, get_search_repository
from app.schemas.search import UserSearchResult

logger = get_logger(__name__)

class SearchService:
    """Service for user search operations."""

    def __init__(self, search_repo: SearchRepository):
        self.search_repo = search_repo

    async def search_users(
        self, 
        query: str, 
        requesting_user_id: UUID, 
        limit: int = 20, 
        offset: int = 0
    ) -> Tuple[List[UserSearchResult], int]:
        """Search users by name or username."""
        results = await self.search_repo.search_users(query, requesting_user_id, limit, offset)

        logger.info("user_search_executed", query=query, results=len(results))
        return results, len(results)

    async def update_last_seen(self, user_id: UUID) -> bool:
        """Update last seen timestamp."""
        success = await self.search_repo.update_last_seen(user_id)
        return success

def get_search_service(repo: SearchRepository = Depends(get_search_repository)) -> SearchService:
    """Dependency provider for SearchService."""
    return SearchService(repo)