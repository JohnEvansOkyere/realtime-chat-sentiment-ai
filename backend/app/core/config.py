# backend/app/core/config.py

"""
Configuration management using Pydantic Settings.
Loads environment variables and provides typed configuration.
Time Complexity: O(1) - Configuration loaded once at startup
Space Complexity: O(1) - Fixed configuration size
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Application
    APP_NAME: str = "Realtime Chat AI"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance
settings = Settings()