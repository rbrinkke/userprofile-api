import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import Database, get_db
from app.core.security import get_current_user, TokenPayload


# Mock Database
class MockDatabase(Database):
    def __init__(self):
        self.pool = MagicMock()
    
    async def connect(self): pass
    async def disconnect(self): pass
    async def fetch_one(self, query, *args): return None
    async def fetch_all(self, query, *args): return []
    async def execute(self, query, *args): return "INSERT 0 1"
    async def fetch_val(self, query, *args): return None


@pytest.fixture
def mock_db():
    db = MockDatabase()
    # Allow setting return values in tests
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    db.execute = AsyncMock(return_value="INSERT 0 1")
    db.fetch_val = AsyncMock(return_value=None)
    return db


@pytest.fixture
def app_fixture(mock_db) -> FastAPI:
    app.dependency_overrides[get_db] = lambda: mock_db
    return app


@pytest_asyncio.fixture
async def client(app_fixture) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app_fixture)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def mock_current_user():
    return TokenPayload({
        "sub": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "org_id": None,
        "subscription_level": "free",
        "ghost_mode": False,
        "exp": 1735689600,
        "type": "access",
        "role": "user"
    })


@pytest.fixture
def authenticated_client(client, mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    return client
