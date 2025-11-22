from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class UserInterests(SQLModel, table=True):
    __tablename__ = "user_interests"
    __table_args__ = {"schema": "activity"}

    user_id: UUID = Field(sa_column=Column(PG_UUID, ForeignKey("activity.users.user_id", ondelete="CASCADE"), primary_key=True))
    interest_tag: str = Field(primary_key=True, max_length=100)

    weight: float = Field(default=1.0)
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))

    user: "User" = Relationship(back_populates="interests")
