# backend/tests/conftest.py
# UPDATE the entire file with this fixed version:

"""
Shared test fixtures and configuration.
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import MagicMock, AsyncMock, patch
import jwt
from datetime import datetime, timedelta

from app.main import app
from app.core.config import settings


# ==================== Fixtures ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator:
    """Create a test client for synchronous tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Create an async test client for async tests."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db():
    """Mock database client for unit tests."""
    mock = MagicMock()
    
    # Mock common database operations
    mock.table.return_value.select.return_value.execute.return_value.data = []
    mock.table.return_value.insert.return_value.execute.return_value.data = []
    mock.table.return_value.update.return_value.execute.return_value.data = []
    mock.table.return_value.delete.return_value.execute.return_value.data = []
    
    return mock


@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "is_active": True,
        "is_admin": False,
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_admin():
    """Sample admin user data for testing."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "email": "admin@example.com",
        "username": "adminuser",
        "full_name": "Admin User",
        "is_active": True,
        "is_admin": True,
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_chat_room():
    """Sample chat room data for testing."""
    return {
        "id": "room-123e4567-e89b-12d3-a456-426614174000",
        "name": "Test Room",
        "is_group": False,
        "created_by": "123e4567-e89b-12d3-a456-426614174000",
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_message():
    """Sample message data for testing."""
    return {
        "id": "msg-123e4567-e89b-12d3-a456-426614174000",
        "content": "Hello, this is a test message!",
        "chat_room_id": "room-123e4567-e89b-12d3-a456-426614174000",
        "sender_id": "123e4567-e89b-12d3-a456-426614174000",
        "message_type": "text",
        "sentiment": "positive",
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def valid_access_token(sample_user):
    """Generate a valid JWT access token for testing."""
    payload = {
        "sub": sample_user["id"],
        "email": sample_user["email"],
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "type": "access"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


@pytest.fixture
def valid_refresh_token(sample_user):
    """Generate a valid JWT refresh token for testing."""
    payload = {
        "sub": sample_user["id"],
        "email": sample_user["email"],
        "exp": datetime.utcnow() + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


@pytest.fixture
def expired_token(sample_user):
    """Generate an expired JWT token for testing."""
    payload = {
        "sub": sample_user["id"],
        "email": sample_user["email"],
        "exp": datetime.utcnow() - timedelta(hours=1),
        "type": "access"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


@pytest.fixture
def admin_access_token(sample_admin):
    """Generate a valid JWT access token for admin user."""
    payload = {
        "sub": sample_admin["id"],
        "email": sample_admin["email"],
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "type": "access"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


@pytest.fixture
def auth_headers(valid_access_token):
    """Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {valid_access_token}"}


@pytest.fixture
def admin_auth_headers(admin_access_token):
    """Authorization headers for admin requests."""
    return {"Authorization": f"Bearer {admin_access_token}"}


@pytest.fixture
def mock_get_current_user(sample_user):
    """Mock the get_current_active_user dependency."""
    from app.schemas.user import UserResponse
    
    def _mock_user():
        return UserResponse(**sample_user)
    
    with patch('app.api.dependencies.get_current_active_user', return_value=_mock_user()):
        yield _mock_user()


@pytest.fixture
def mock_get_admin_user(sample_admin):
    """Mock the get_admin_user dependency."""
    from app.schemas.user import UserResponse
    
    def _mock_admin():
        return UserResponse(**sample_admin)
    
    with patch('app.api.analytics.get_admin_user', return_value=_mock_admin()):
        yield _mock_admin()


# ==================== Helper Functions ====================

@pytest.fixture
def create_test_user():
    """Factory fixture for creating test users."""
    def _create_user(
        email="test@example.com",
        username="testuser",
        is_admin=False
    ):
        return {
            "id": f"user-{email}",
            "email": email,
            "username": username,
            "full_name": f"Test {username}",
            "is_active": True,
            "is_admin": is_admin,
            "created_at": datetime.utcnow().isoformat()
        }
    return _create_user


@pytest.fixture
def override_get_current_user(sample_user):
    """Override dependency to return test user."""
    from app.schemas.user import UserResponse
    from app.api.dependencies import get_current_active_user
    
    async def _get_test_user():
        return UserResponse(**sample_user)
    
    app.dependency_overrides[get_current_active_user] = _get_test_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def override_get_admin_user(sample_admin):
    """Override dependency to return admin user."""
    from app.schemas.user import UserResponse
    from app.api.dependencies import get_current_active_user
    
    async def _get_test_admin():
        return UserResponse(**sample_admin)
    
    app.dependency_overrides[get_current_active_user] = _get_test_admin
    yield
    app.dependency_overrides.clear()