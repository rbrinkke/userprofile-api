from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.database import Database
from app.schemas.common import SubscriptionLevel
from app.schemas.subscription import SubscriptionResponse


class SubscriptionRepository:
    def __init__(self, db: Database):
        self.db = db

    async def get(self, user_id: UUID) -> Optional[SubscriptionResponse]:
        """
        Get subscription details.
        """
        result = await self.db.fetch_one(
            "SELECT subscription_level, subscription_expires_at, is_captain, captain_since FROM activity.users WHERE user_id = $1",
            user_id
        )
        if not result:
            return None
        return SubscriptionResponse(**result)

    async def update(self, user_id: UUID, subscription_level: SubscriptionLevel, expires_at: Optional[datetime]) -> bool:
        """
        Update subscription level.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_update_subscription($1, $2, $3)",
            user_id, subscription_level.value, expires_at
        )
        return bool(result and result.get("success"))

    async def set_captain_status(self, user_id: UUID, is_captain: bool) -> bool:
        """
        Grant/revoke captain status.
        """
        result = await self.db.fetch_one(
            "SELECT * FROM activity.sp_set_captain_status($1, $2)",
            user_id, is_captain
        )
        return bool(result and result.get("success"))
