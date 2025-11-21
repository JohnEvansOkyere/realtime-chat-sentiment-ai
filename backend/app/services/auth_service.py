# backend/app/services/auth_service.py

"""
Authentication service handling user registration, login, and session management.
Time Complexity:
    - register_user: O(1) - Single database insert
    - authenticate_user: O(1) - Single database query
    - get_current_user: O(1) - Single database query
Space Complexity: O(1) for all operations
"""
from typing import Optional, Dict, Any
from datetime import datetime
from ..core.security import security_service
from ..models.database import db_service
from ..schemas.user import UserCreate, UserResponse, TokenResponse


class AuthenticationService:
    """Handles all authentication-related operations."""
    
    def __init__(self):
        """Initialize with database service."""
        self.db = db_service.get_admin_client()
    
    async def register_user(self, user_data: UserCreate) -> TokenResponse:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            TokenResponse with access and refresh tokens
            
        Raises:
            ValueError: If user already exists
        """
        # Check if user exists
        existing_user = self.db.table('users').select('id').eq('email', user_data.email).execute()
        if existing_user.data:
            raise ValueError("User with this email already exists")
        
        existing_username = self.db.table('users').select('id').eq('username', user_data.username).execute()
        if existing_username.data:
            raise ValueError("Username already taken")
        
        # Hash password
        hashed_password = security_service.hash_password(user_data.password)
        
        # Create user
        user_dict = {
            'email': user_data.email,
            'username': user_data.username,
            'full_name': user_data.full_name,
            'hashed_password': hashed_password,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = self.db.table('users').insert(user_dict).execute()
        
        if not result.data:
            raise ValueError("Failed to create user")
        
        created_user = result.data[0]
        
        # Generate tokens
        token_data = {"sub": created_user['id'], "email": created_user['email']}
        access_token = security_service.create_access_token(token_data)
        refresh_token = security_service.create_refresh_token(token_data)
        
        user_response = UserResponse(**created_user)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_response
        )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[TokenResponse]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            TokenResponse if successful, None otherwise
        """
        # Get user by email
        result = self.db.table('users').select('*').eq('email', email).execute()
        
        if not result.data:
            return None
        
        user = result.data[0]
        
        # Verify password
        if not security_service.verify_password(password, user['hashed_password']):
            return None
        
        # Check if user is active
        if not user.get('is_active', True):
            return None
        
        # Generate tokens
        token_data = {"sub": user['id'], "email": user['email']}
        access_token = security_service.create_access_token(token_data)
        refresh_token = security_service.create_refresh_token(token_data)
        
        # Remove sensitive data
        user.pop('hashed_password', None)
        user_response = UserResponse(**user)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_response
        )
    
    async def get_current_user(self, token: str) -> Optional[UserResponse]:
        """
        Get current user from access token.
        
        Args:
            token: JWT access token
            
        Returns:
            UserResponse if valid, None otherwise
        """
        payload = security_service.decode_token(token)
        
        if not payload or payload.get('type') != 'access':
            return None
        
        user_id = payload.get('sub')
        if not user_id:
            return None
        
        # Get user from database
        result = self.db.table('users').select('*').eq('id', user_id).execute()
        
        if not result.data:
            return None
        
        user = result.data[0]
        user.pop('hashed_password', None)
        
        return UserResponse(**user)
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[TokenResponse]:
        """
        Generate new access token from refresh token.
        
        Args:
            refresh_token: JWT refresh token
            
        Returns:
            New TokenResponse with fresh tokens
        """
        payload = security_service.decode_token(refresh_token)
        
        if not payload or payload.get('type') != 'refresh':
            return None
        
        user_id = payload.get('sub')
        email = payload.get('email')
        
        if not user_id or not email:
            return None
        
        # Verify user still exists and is active
        result = self.db.table('users').select('*').eq('id', user_id).execute()
        
        if not result.data or not result.data[0].get('is_active', True):
            return None
        
        user = result.data[0]
        
        # Generate new tokens
        token_data = {"sub": user_id, "email": email}
        new_access_token = security_service.create_access_token(token_data)
        new_refresh_token = security_service.create_refresh_token(token_data)
        
        user.pop('hashed_password', None)
        user_response = UserResponse(**user)
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user=user_response
        )


# Singleton instance
auth_service = AuthenticationService()