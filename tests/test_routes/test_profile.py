import pytest
from uuid import UUID
from datetime import datetime

@pytest.mark.asyncio
async def test_get_my_profile(authenticated_client, mock_db):
    # Setup mock DB response
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    mock_profile_data = {
        "user_id": user_id,
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "profile_description": "Bio",
        "main_photo_url": None,
        "main_photo_moderation_status": "approved",
        "profile_photos_extra": [],  # List, so repo won't parse it (it expects str if from DB)
        "date_of_birth": datetime(1990, 1, 1),
        "gender": "other",
        "subscription_level": "free",
        "subscription_expires_at": None,
        "is_captain": False,
        "captain_since": None,
        "is_verified": False,
        "verification_count": 0,
        "no_show_count": 0,
        "activities_created_count": 0,
        "activities_attended_count": 0,
        "created_at": datetime(2023, 1, 1, 0, 0, 0),
        "last_seen_at": None,
        "interests": [], # List
        "settings": {}   # Dict
    }
    
    # Mock the DB call
    # The repo calls fetch_one with specific query
    mock_db.fetch_one.return_value = mock_profile_data

    response = await authenticated_client.get("/api/v1/users/me")
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["user_id"] == user_id
