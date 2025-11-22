from typing import List
from uuid import UUID
from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete, func

from app.core.database import get_db
from app.models.interests import UserInterests
from app.schemas.common import InterestTag
from app.schemas.interests import SetInterestsResponse, AddInterestResponse, RemoveInterestResponse

class InterestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: UUID) -> List[InterestTag]:
        """
        Fetch user interests from database.
        """
        query = select(UserInterests).where(UserInterests.user_id == user_id)
        result = await self.session.execute(query)
        interests = result.scalars().all()

        return [InterestTag(tag=i.interest_tag, weight=i.weight) for i in interests]

    async def set_interests(self, user_id: UUID, interests: List[InterestTag]) -> SetInterestsResponse:
        """
        Set all interests (replaces existing).
        """
        # Check limit (max 20)
        if len(interests) > 20:
             return SetInterestsResponse(
                success=False,
                interest_count=0,
                interests=[],
                message="Cannot have more than 20 interests"
            )

        try:
            # Transaction start
            # Delete existing
            await self.session.execute(delete(UserInterests).where(UserInterests.user_id == user_id))

            # Bulk insert
            new_interests = [
                UserInterests(user_id=user_id, interest_tag=i.tag, weight=i.weight)
                for i in interests
            ]
            self.session.add_all(new_interests)

            await self.session.commit()

            return SetInterestsResponse(
                success=True,
                interest_count=len(interests),
                interests=interests
            )
        except Exception as e:
            await self.session.rollback()
            # Log error
            return SetInterestsResponse(success=False, interest_count=0, interests=[])

    async def add_interest(self, user_id: UUID, tag: str, weight: float) -> AddInterestResponse:
        """
        Add single interest.
        """
        # Check count
        query_count = select(func.count()).select_from(UserInterests).where(UserInterests.user_id == user_id)
        result = await self.session.execute(query_count)
        count = result.scalar_one()

        if count >= 20:
             return AddInterestResponse(success=False, message="Maximum limit of 20 interests reached")

        # Upsert logic (Insert or Update)
        # Check if exists
        query_exist = select(UserInterests).where(UserInterests.user_id == user_id, UserInterests.interest_tag == tag)
        result_exist = await self.session.execute(query_exist)
        existing = result_exist.scalar_one_or_none()

        if existing:
            existing.weight = weight
            existing.updated_at = datetime.now()
            msg = "Interest updated"
        else:
            new_interest = UserInterests(user_id=user_id, interest_tag=tag, weight=weight)
            self.session.add(new_interest)
            msg = "Interest added"

        await self.session.commit()
        
        return AddInterestResponse(
            success=True,
            message=msg
        )

    async def remove_interest(self, user_id: UUID, tag: str) -> RemoveInterestResponse:
        """
        Remove single interest.
        """
        query = delete(UserInterests).where(UserInterests.user_id == user_id, UserInterests.interest_tag == tag)
        result = await self.session.execute(query)
        await self.session.commit()
        
        if result.rowcount > 0:
             return RemoveInterestResponse(
                 success=True,
                 message="Interest removed"
             )
        return RemoveInterestResponse(success=False, message="Interest not found")

def get_interest_repository(session: AsyncSession = Depends(get_db)) -> InterestRepository:
    return InterestRepository(session)
