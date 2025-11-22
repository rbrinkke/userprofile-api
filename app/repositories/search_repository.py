from typing import List, Tuple
from uuid import UUID
from datetime import datetime

from fastapi import Depends
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_, func, and_

from app.core.database import get_db
from app.models.user import User
from app.models.blocking import UserBlock
from app.schemas.search import UserSearchResult

class SearchRepository:
    search_result_adapter = TypeAdapter(List[UserSearchResult])

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_users(
        self,
        query_str: str,
        requesting_user_id: UUID,
        limit: int,
        offset: int
    ) -> List[UserSearchResult]:
        """
        Search users by name or username.
        """
        # Subquery to find blocked relationships (either blocked by me or blocked me)
        # We select user_id from UserBlock where (blocker = me AND blocked = user) OR (blocker = user AND blocked = me)
        # Instead of notin_, we can use NOT EXISTS logic

        subquery_blocked_by_me = (
            select(UserBlock.blocked_user_id)
            .where(UserBlock.blocker_user_id == requesting_user_id)
        )
        subquery_blocked_me = (
            select(UserBlock.blocker_user_id)
            .where(UserBlock.blocked_user_id == requesting_user_id)
        )

        query = (
            select(User)
            .where(
                or_(
                    func.lower(User.username).contains(query_str.lower()),
                    func.lower(User.first_name).contains(query_str.lower()),
                    func.lower(User.last_name).contains(query_str.lower())
                )
            )
            .where(User.user_id != requesting_user_id) # Exclude self
            .where(User.user_id.notin_(subquery_blocked_by_me))
            .where(User.user_id.notin_(subquery_blocked_me))
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        users = result.scalars().all()

        # Transform to UserSearchResult
        return [
            UserSearchResult(
                user_id=u.user_id,
                username=u.username,
                first_name=u.first_name,
                last_name=u.last_name,
                main_photo_url=u.main_photo_url,
                is_verified=u.is_verified
            )
            for u in users
        ]

    async def update_last_seen(self, user_id: UUID) -> bool:
        """
        Update last seen timestamp.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.last_seen_at = datetime.now()
        try:
            await self.session.commit()
            return True
        except Exception:
            return False

def get_search_repository(session: AsyncSession = Depends(get_db)) -> SearchRepository:
    return SearchRepository(session)
