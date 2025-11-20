from typing import Dict, Any, Optional
from uuid import UUID

from app.core.database import Database

class VerificationRepository:
    def __init__(self, db: Database):
        self.db = db

    async def get_metrics(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get verification metrics from user table.
        """
        result = await self.db.fetch_one(
            "SELECT verification_count, no_show_count, is_verified, activities_attended_count FROM activity.users WHERE user_id = $1",
            user_id
        )
        return dict(result) if result else None

    async def increment_verification(self, user_id: UUID) -> Dict[str, Any]:
        """
        Increment verification count.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_increment_verification_count($1)",
            user_id
        )
        return dict(result) if result else {}

    async def increment_no_show(self, user_id: UUID) -> Dict[str, Any]:
        """
        Increment no-show count.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_increment_no_show_count($1)",
            user_id
        )
        return dict(result) if result else {}

    async def update_activity_counters(self, user_id: UUID, created_delta: int, attended_delta: int) -> Dict[str, Any]:
        """
        Update activity counters.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_update_activity_counts($1, $2, $3)",
            user_id, created_delta, attended_delta
        )
        return dict(result) if result else {}
