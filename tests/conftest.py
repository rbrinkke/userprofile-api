import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.core.security import get_current_user, TokenPayload


# Mock AsyncSession
# We need to mock execute, scalar_one_or_none, scalars, etc.
class MockAsyncSession(AsyncMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execute_result = AsyncMock()
        self.execute_result.scalar_one_or_none.return_value = None
        self.execute_result.scalars.return_value.all.return_value = []
        self.execute.return_value = self.execute_result

    async def commit(self): pass
    async def rollback(self): pass
    async def refresh(self, instance): pass
    async def close(self): pass
    def add(self, instance): pass
    def add_all(self, instances): pass


@pytest.fixture
def mock_session():
    session = MockAsyncSession(spec=AsyncSession)
    return session


@pytest.fixture
def app_fixture(mock_session) -> FastAPI:
    # Override the get_db dependency to yield our mock session
    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
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
