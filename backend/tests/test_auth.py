# backend/tests/test_auth.py
"""
Unit tests for authentication endpoints.
Coverage: Registration, Login, Token Refresh, User Info
"""
import pytest
from unittest.mock import patch, MagicMock
import bcrypt
from fastapi import status


class TestUserRegistration:
    """Tests for user registration endpoint."""
    
    def test_register_duplicate_email(self, client, mock_db):
        """Test registration with existing email."""
        with patch('app.models.database.db_service.get_admin_client', return_value=mock_db):
            # Mock user already exists
            mock_db.table.return_value.select.return_value.execute.return_value.data = [{
                "id": "existing-user",
                "email": "existing@example.com",
                "username": "existinguser"
            }]
            
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "existing@example.com",
                    "username": "newuser",
                    "password": "securepassword123"
                }
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            # Match actual error message from your code
            assert ("already" in response.json()["detail"].lower() or 
                    "taken" in response.json()["detail"].lower())
    
    def test_register_duplicate_email(self, client, mock_db):
        """Test registration with existing email."""
        with patch('app.services.auth_service.db_service.get_admin_client', return_value=mock_db):
            # Mock user already exists
            mock_db.table.return_value.select.return_value.execute.return_value.data = [{
                "id": "existing-user",
                "email": "existing@example.com"
            }]
            
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "existing@example.com",
                    "username": "newuser",
                    "password": "securepassword123"
                }
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "already registered" in response.json()["detail"].lower()
    
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
    
    def test_register_short_password(self, client):
        """Test registration with password too short."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "short"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com"
                # Missing username and password
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserLogin:
    """Tests for user login endpoint."""
    
    def test_login_success(self, client, mock_db, sample_user):
        """Test successful user login."""
        import bcrypt
        
        # Hash a test password
        test_password = "testpassword123"
        hashed_password = bcrypt.hashpw(test_password.encode(), bcrypt.gensalt())
        
        with patch('app.models.database.db_service.get_admin_client', return_value=mock_db):
            # Mock user exists with hashed password
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
                **sample_user,
                "hashed_password": hashed_password.decode()
            }
            
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": sample_user["email"],
                    "password": test_password
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["email"] == sample_user["email"]
    
    def test_login_invalid_email(self, client, mock_db):
        """Test login with non-existent email."""
        with patch('app.models.database.db_service.get_admin_client', return_value=mock_db):
            # Mock user doesn't exist
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
            
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "nonexistent@example.com",
                    "password": "anypassword"
                }
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_wrong_password(self, client, mock_db, sample_user):
        """Test login with incorrect password."""
        import bcrypt
        
        correct_password = "correctpassword"
        hashed_password = bcrypt.hashpw(correct_password.encode(), bcrypt.gensalt())
        
        with patch('app.models.database.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
                **sample_user,
                "hashed_password": hashed_password.decode()
            }
            
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": sample_user["email"],
                    "password": "wrongpassword"
                }
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_inactive_user(self, client, mock_db, sample_user):
        """Test login with inactive user account."""
        import bcrypt
        
        test_password = "testpassword123"
        hashed_password = bcrypt.hashpw(test_password.encode(), bcrypt.gensalt())
        
        with patch('app.models.database.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
                **sample_user,
                "is_active": False,
                "hashed_password": hashed_password.decode()
            }
            
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": sample_user["email"],
                    "password": test_password
                }
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "inactive" in response.json()["detail"].lower()


class TestTokenRefresh:
    """Tests for token refresh endpoint."""
    
    def test_refresh_token_success(self, client, valid_refresh_token, mock_db, sample_user):
        """Test successful token refresh."""
        with patch('app.services.auth_service.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_user
            
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": valid_refresh_token}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
    
    def test_refresh_with_expired_token(self, client, expired_token):
        """Test token refresh with expired refresh token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_token}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_with_invalid_token(self, client):
        """Test token refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetCurrentUser:
    """Tests for get current user endpoint."""
    
    def test_get_current_user_success(self, client, auth_headers, mock_db, sample_user):
        """Test getting current user info with valid token."""
        with patch('app.services.auth_service.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_user
            
            response = client.get(
                "/api/v1/auth/me",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == sample_user["email"]
            assert data["username"] == sample_user["username"]
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_expired_token(self, client, expired_token):
        """Test getting current user with expired token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPasswordSecurity:
    """Tests for password hashing and security."""
    
    def test_password_hashed(self, client, mock_db):
        """Test that passwords are properly hashed."""
        plain_password = "myplainpassword"
        
        with patch('app.services.auth_service.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.execute.return_value.data = []
            
            def capture_insert(data):
                # Verify password is hashed
                assert "hashed_password" in data
                assert data["hashed_password"] != plain_password
                assert data["hashed_password"].startswith("$2b$")
                return MagicMock(data=[{**data, "id": "new-user"}])
            
            mock_db.table.return_value.insert.return_value.execute.side_effect = capture_insert
            
            client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": plain_password
                }
            )
    
    def test_bcrypt_rounds(self):
        """Test that bcrypt uses sufficient rounds."""
        password = "testpassword"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
        
        # Verify it uses 12 rounds (format: $2b$12$...)
        assert hashed.decode().startswith("$2b$12$")