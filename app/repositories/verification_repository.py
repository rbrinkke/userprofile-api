from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_db
from app.models.user import User

class VerificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_metrics(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get verification metrics from user table.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        return {
            "verification_count": user.verification_count,
            "no_show_count": user.no_show_count,
            "is_verified": user.is_verified,
            "activities_attended_count": user.activities_attended_count
        }

    async def increment_verification(self, user_id: UUID) -> Dict[str, Any]:
        """
        Increment verification count.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return {"success": False}

        user.verification_count += 1
        # Logic from SP might include: if verification_count > threshold, set is_verified = True
        # Assuming threshold is configurable or hardcoded. Old SP logic isn't visible.
        # I'll assume a reasonable threshold or leave it to a separate process if not sure.
        # Actually the schema comment says "Number of successful attendance verifications".

        user.updated_at = datetime.now()
        await self.session.commit()

        return {"success": True, "new_count": user.verification_count}

    async def increment_no_show(self, user_id: UUID) -> Dict[str, Any]:
        """
        Increment no-show count.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return {"success": False}

        user.no_show_count += 1
        user.updated_at = datetime.now()
        await self.session.commit()

        return {"success": True, "new_count": user.no_show_count}

    async def update_activity_counters(self, user_id: UUID, created_delta: int, attended_delta: int) -> Dict[str, Any]:
        """
        Update activity counters.
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return {"success": False}

        user.activities_created_count = max(0, user.activities_created_count + created_delta)
        user.activities_attended_count = max(0, user.activities_attended_count + attended_delta)
        user.updated_at = datetime.now()

        await self.session.commit()

        return {
            "success": True,
            "created_count": user.activities_created_count,
            "attended_count": user.activities_attended_count
        }

def get_verification_repository(session: AsyncSession = Depends(get_db)) -> VerificationRepository:
    return VerificationRepository(session)
