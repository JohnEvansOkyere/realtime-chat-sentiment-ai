# backend/app/api/auth.py

"""
Authentication API endpoints.
Time Complexity: O(1) per endpoint (single DB operation)
Space Complexity: O(1)
"""
from fastapi import APIRouter, HTTPException, status, Depends
from ..schemas.user import UserCreate, UserLogin, TokenResponse, TokenRefresh, UserResponse, PasswordResetSimple 
from ..services.auth_service import auth_service
from .dependencies import get_current_active_user
#from ..schemas.user import PasswordResetRequest, PasswordResetConfirm, PasswordResetResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register-admin", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_admin(
    user_data: UserCreate,
    admin_secret: str  # Pass a secret key to verify
):
    """
    Register a new admin user (requires admin secret).
    Only use this for initial admin setup!
    """
    from ..core.config import settings
    
    # Check admin secret (set in .env: ADMIN_SECRET_KEY=your-secret)
    if admin_secret != "your-super-secret-admin-key":  # Use settings.ADMIN_SECRET_KEY in production
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin secret"
        )
    
    # Create admin user (modify auth_service.register_user to accept is_admin param)
    # For now, create normally then update
    result = await auth_service.register_user(user_data)
    
    # Update to admin
    db = db_service.get_admin_client()
    db.table('users').update({'is_admin': True}).eq('id', result.user.id).execute()
    
    return result

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
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


@router.post("/reset-password-simple")
async def reset_password_simple(reset_data: PasswordResetSimple):
    """
    Simple password reset - just email + new password (NO email verification)
    ⚠️ Less secure but simpler for development
    """
    success = await auth_service.reset_password_simple(
        reset_data.email,
        reset_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="No account found with this email address"
        )
    
    return {
        "message": "Password updated successfully. You can now login with your new password."
    }