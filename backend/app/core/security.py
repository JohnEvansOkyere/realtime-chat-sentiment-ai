# backend/app/core/security.py 

"""
Security utilities for password hashing and JWT token management.
Time Complexity: 
    - Hash password: O(n) where n is password length
    - Verify password: O(n) where n is password length
    - Create token: O(1)
Space Complexity: O(1) for all operations
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings


class SecurityService:
    """Handles all security-related operations."""
    
    def __init__(self):
        """Initialize password context for hashing."""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Payload to encode in token
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token with longer expiration.
        
        Args:
            data: Payload to encode in token
            
        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and verify a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None


# Singleton instance
security_service = SecurityService()