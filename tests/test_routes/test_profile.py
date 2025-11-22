import pytest
from uuid import UUID
from datetime import datetime
from unittest.mock import MagicMock
from app.models.user import User
from app.models.settings import UserSettings
from app.models.interests import UserInterests

@pytest.mark.asyncio
async def test_get_my_profile(authenticated_client, mock_session):
    # Setup mock DB response
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    
    # Create mock user object
    mock_user = User(
        user_id=user_id,
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        profile_description="Bio",
        main_photo_url=None,
        main_photo_moderation_status="approved",
        profile_photos_extra=[],
        date_of_birth=datetime(1990, 1, 1).date(),
        gender="other",
        subscription_level="free",
        subscription_expires_at=None,
        is_captain=False,
        captain_since=None,
        is_verified=False,
        verification_count=0,
        no_show_count=0,
        activities_created_count=0,
        activities_attended_count=0,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        last_seen_at=None,
        password_hash="dummy"
    )

    # Mock relationships
    mock_user.settings = UserSettings(
        user_id=user_id,
        email_notifications=True,
        push_notifications=True,
        activity_reminders=True,
        community_updates=True,
        friend_requests=True,
        marketing_emails=False,
        ghost_mode=False,
        language="en",
        timezone="Europe/Amsterdam"
    )
    mock_user.interests = []

    # Mock the session execution
    # The first query in ProfileRepository.get_by_user_id is checking blocks
    # The second query is fetching the user

    # We need to handle multiple calls to execute
    # 1. Block check -> returns empty (no blocks)
    # 2. User fetch -> returns mock_user

    async def side_effect(query):
        # Basic string check to identify queries
        # This is brittle but sufficient for simple unit test mocking without a full SQL parser
        query_str = str(query)
        if "user_blocks" in query_str:
            # Block check
            mock_result = MagicMock()
            mock_result.first.return_value = None # No blocks
            return mock_result
        elif "FROM activity.users" in query_str:
             # User fetch
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            return mock_result
        return MagicMock()

    mock_session.execute.side_effect = side_effect

    response = await authenticated_client.get("/api/v1/users/me")
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["user_id"] == str(user_id)
