# backend/tests/test_auth.py
"""
Unit tests for authentication endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock
import bcrypt
from fastapi import status


class TestUserRegistration:
    """Tests for user registration endpoint."""
    
    def test_register_success(self, client, sample_user):
        """Test successful user registration."""
        from app.schemas.user import TokenResponse, UserResponse
        
        mock_response = TokenResponse(
            access_token="fake_access_token",
            refresh_token="fake_refresh_token",
            token_type="bearer",
            user=UserResponse(**sample_user)
        )
        
        with patch('app.api.auth.auth_service.register_user', new_callable=AsyncMock) as mock_register:
            mock_register.return_value = mock_response
            
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "username": "newuser",
                    "full_name": "New User",
                    "password": "securepassword123"
                }
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
    
    def test_register_duplicate_email(self, client):
        """Test registration with existing email or username."""
        with patch('app.api.auth.auth_service.register_user', new_callable=AsyncMock) as mock_register:
            mock_register.side_effect = ValueError("Email already registered")
            
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "existing@example.com",
                    "username": "newuser",
                    "password": "securepassword123"
                }
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserLogin:
    """Tests for user login endpoint."""
    
    def test_login_success(self, client, sample_user):
        """Test successful user login."""
        from app.schemas.user import TokenResponse, UserResponse
        
        mock_response = TokenResponse(
            access_token="fake_access_token",
            refresh_token="fake_refresh_token",
            token_type="bearer",
            user=UserResponse(**sample_user)
        )
        
        with patch('app.api.auth.auth_service.authenticate_user', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_response
            
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": sample_user["email"],
                    "password": "testpassword123"
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with wrong credentials."""
        with patch('app.api.auth.auth_service.authenticate_user', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None
            
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "wrong@example.com",
                    "password": "wrongpassword"
                }
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "incorrect email or password" in response.json()["detail"].lower()


class TestTokenRefresh:
    """Tests for token refresh endpoint."""
    
    def test_refresh_token_success(self, client, sample_user):
        """Test successful token refresh."""
        from app.schemas.user import TokenResponse, UserResponse
        
        mock_response = TokenResponse(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            token_type="bearer",
            user=UserResponse(**sample_user)
        )
        
        with patch('app.api.auth.auth_service.refresh_access_token', new_callable=AsyncMock) as mock_refresh:
            mock_refresh.return_value = mock_response
            
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid_refresh_token"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
    
    def test_refresh_with_invalid_token(self, client):
        """Test token refresh with invalid token."""
        with patch('app.api.auth.auth_service.refresh_access_token', new_callable=AsyncMock) as mock_refresh:
            mock_refresh.return_value = None
            
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid.token.here"}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetCurrentUser:
    """Tests for get current user endpoint."""
    
    def test_get_current_user_success(self, authenticated_client, sample_user):
        """Test getting current user info."""
        response = authenticated_client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == sample_user["email"]
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN