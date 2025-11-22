from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

class UserBlock(SQLModel, table=True):
    __tablename__ = "user_blocks"
    __table_args__ = {"schema": "activity"}

    blocker_user_id: UUID = Field(sa_column=Column(PG_UUID, ForeignKey("activity.users.user_id", ondelete="CASCADE"), primary_key=True))
    blocked_user_id: UUID = Field(sa_column=Column(PG_UUID, ForeignKey("activity.users.user_id", ondelete="CASCADE"), primary_key=True))

    reason: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))

    payload: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
