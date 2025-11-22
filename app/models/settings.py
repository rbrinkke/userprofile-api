from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

class UserSettings(SQLModel, table=True):
    __tablename__ = "user_settings"
    __table_args__ = {"schema": "activity"}

    user_id: UUID = Field(sa_column=Column(PG_UUID, ForeignKey("activity.users.user_id", ondelete="CASCADE"), primary_key=True))

    email_notifications: bool = Field(default=True)
    push_notifications: bool = Field(default=True)
    activity_reminders: bool = Field(default=True)
    community_updates: bool = Field(default=True)
    friend_requests: bool = Field(default=True)
    marketing_emails: bool = Field(default=False)
    ghost_mode: bool = Field(default=False)
    language: str = Field(default="en", max_length=10)
    timezone: str = Field(default="UTC", max_length=50)

    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))

    payload: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    hash_value: Optional[str] = Field(default=None, max_length=64)

    user: "User" = Relationship(back_populates="settings")
