# backend/app/models/database.py

"""
Database models and Supabase client initialization.
Time Complexity: O(1) for client initialization
Space Complexity: O(1)
"""
from supabase import create_client, Client
from ..core.config import settings


class DatabaseService:
    """Service for database operations using Supabase."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.admin_client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
    
    def get_client(self) -> Client:
        """Get regular Supabase client."""
        return self.client
    
    def get_admin_client(self) -> Client:
        """Get admin Supabase client with elevated privileges."""
        return self.admin_client


# Singleton instance
db_service = DatabaseService()