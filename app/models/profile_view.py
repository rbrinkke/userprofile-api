from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

class ProfileView(SQLModel, table=True):
    __tablename__ = "profile_views"
    __table_args__ = {"schema": "activity"}

    view_id: UUID = Field(default_factory=uuid4, sa_column=Column(PG_UUID, primary_key=True))
    viewer_user_id: UUID = Field(sa_column=Column(PG_UUID, ForeignKey("activity.users.user_id", ondelete="CASCADE"), nullable=False))
    viewed_user_id: UUID = Field(sa_column=Column(PG_UUID, ForeignKey("activity.users.user_id", ondelete="CASCADE"), nullable=False))

    viewed_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))

    payload: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
