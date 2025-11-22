# backend/tests/conftest.py
"""
Shared test fixtures and configuration.
"""
import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import jwt
from datetime import datetime, timedelta

from app.main import app
from app.core.config import settings
from app.schemas.user import UserResponse


# ==================== App Setup ====================

@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    """Reset dependency overrides after each test."""
    yield
    app.dependency_overrides.clear()


# ==================== Fixtures ====================

@pytest.fixture
def client() -> Generator:
    """Create a test client for synchronous tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_db():
    """Mock database client for unit tests."""
    mock = MagicMock()
    
    # Mock common database operations
    mock.table.return_value.select.return_value.execute.return_value.data = []
    mock.table.return_value.insert.return_value.execute.return_value.data = []
    mock.table.return_value.update.return_value.execute.return_value.data = []
    mock.table.return_value.delete.return_value.execute.return_value.data = []
    mock.table.return_value.select.return_value.execute.return_value.count = 0
    
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


# ==================== Authentication Fixtures ====================

@pytest.fixture
def authenticated_client(client, sample_user):
    """Client with authentication dependency overridden."""
    from app.api.dependencies import get_current_active_user
    
    async def override_get_current_user():
        return UserResponse(**sample_user)
    
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    return client


@pytest.fixture
def admin_client(client, sample_admin):
    """Client with admin authentication dependency overridden."""
    from app.api.dependencies import get_current_active_user
    
    async def override_get_admin_user():
        return UserResponse(**sample_admin)
    
    app.dependency_overrides[get_current_active_user] = override_get_admin_user
    return client


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