from typing import Optional, List, Any
from uuid import UUID, uuid4
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, Text, Boolean, Integer, Date, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from geoalchemy2 import Geography
from enum import Enum

# Enums need to be defined or imported.
# For simplicity, I will define string-based enums where appropriate or use simple strings if strict enum checking is not required by ORM.
# However, using Enum classes is better for type safety.

class SubscriptionLevel(str, Enum):
    free = "free"
    club = "club"
    premium = "premium"

class UserStatus(str, Enum):
    active = "active"
    temporary_ban = "temporary_ban"
    banned = "banned"

class PhotoModerationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "activity"}

    user_id: UUID = Field(default_factory=uuid4, sa_column=Column(PG_UUID, primary_key=True))
    email: str = Field(unique=True, max_length=255, nullable=False)
    username: str = Field(unique=True, max_length=100, nullable=False)
    password_hash: str = Field(max_length=255, nullable=False)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)

    # Profile fields
    profile_description: Optional[str] = Field(default=None, sa_column=Column(Text))
    main_photo_url: Optional[str] = Field(default=None, max_length=500)
    main_photo_moderation_status: PhotoModerationStatus = Field(default=PhotoModerationStatus.pending)
    profile_photos_extra: List[str] = Field(default=[], sa_column=Column(JSONB))
    date_of_birth: Optional[date] = Field(default=None)
    gender: Optional[str] = Field(default=None, max_length=50)

    # Subscription & Status
    subscription_level: SubscriptionLevel = Field(default=SubscriptionLevel.free)
    subscription_expires_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    status: UserStatus = Field(default=UserStatus.active)
    ban_expires_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    ban_reason: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Captain program
    is_captain: bool = Field(default=False)
    captain_since: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))

    # Activity tracking
    last_seen_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    activities_created_count: int = Field(default=0)
    activities_attended_count: int = Field(default=0)

    # Verification & trust
    is_verified: bool = Field(default=False)
    verification_count: int = Field(default=0)
    no_show_count: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    last_login_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))

    # Flexible storage
    payload: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    hash_value: Optional[str] = Field(default=None, max_length=64)

    # Location
    location: Optional[Any] = Field(default=None, sa_column=Column(Geography(geometry_type="POINT", srid=4326)))

    # Relationships
    settings: Optional["UserSettings"] = Relationship(sa_relationship_kwargs={"uselist": False}, back_populates="user")
    interests: List["UserInterests"] = Relationship(back_populates="user")
