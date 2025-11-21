# backend/app/api/auth.py

"""
Authentication API endpoints.
Time Complexity: O(1) per endpoint (single DB operation)
Space Complexity: O(1)
"""
from fastapi import APIRouter, HTTPException, status, Depends
from ..schemas.user import UserCreate, UserLogin, TokenResponse, TokenRefresh, UserResponse
from ..services.auth_service import auth_service
from .dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.
    
    Business Value: Enables user onboarding for the chat platform
    """
    try:
        return await auth_service.register_user(user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Authenticate user and return tokens.
    
    Business Value: Secure user authentication with JWT tokens
    """
    result = await auth_service.authenticate_user(credentials.email, credentials.password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh):
    """
    Refresh access token using refresh token.
    
    Business Value: Seamless session management without re-login
    """
    result = await auth_service.refresh_access_token(token_data.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_active_user)):
    """
    Get current user information.
    
    Business Value: Check session validity and get user profile
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: UserResponse = Depends(get_current_active_user)):
    """
    Logout current user (client should discard tokens).
    
    Business Value: Explicit session termination
    """
    return {"message": "Successfully logged out"}