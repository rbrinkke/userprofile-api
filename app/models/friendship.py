from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

class Friendship(SQLModel, table=True):
    __tablename__ = "friendships"
    __table_args__ = {"schema": "activity"}

    user_id_1: UUID = Field(sa_column=Column(PG_UUID, ForeignKey("activity.users.user_id", ondelete="CASCADE"), primary_key=True))
    user_id_2: UUID = Field(sa_column=Column(PG_UUID, ForeignKey("activity.users.user_id", ondelete="CASCADE"), primary_key=True))

    status: str = Field(default="pending", max_length=20)
    initiated_by: UUID = Field(sa_column=Column(PG_UUID, ForeignKey("activity.users.user_id"), nullable=False))

    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    accepted_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))

    payload: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    hash_value: Optional[str] = Field(default=None, max_length=64)
