# backend/tests/test_services.py
"""
Unit tests for service layer.
Coverage: AuthService, ChatService business logic
"""
import pytest
from unittest.mock import patch, MagicMock
import bcrypt


class TestAuthService:
    """Tests for AuthService business logic."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, mock_db, sample_user):
        """Test user registration service."""
        from app.services.auth_service import AuthService
        from app.schemas.user import UserCreate
        
        with patch('app.services.auth_service.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.execute.return_value.data = []
            mock_db.table.return_value.insert.return_value.execute.return_value.data = [sample_user]
            
            auth_service = AuthService()
            user_data = UserCreate(
                email="new@example.com",
                username="newuser",
                password="password123"
            )
            
            result = await auth_service.register_user(user_data)
            
            assert result.access_token is not None
            assert result.refresh_token is not None
            assert result.user.email == user_data.email
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, mock_db, sample_user):
        """Test registration with existing email."""
        from app.services.auth_service import AuthService
        from app.schemas.user import UserCreate
        
        with patch('app.services.auth_service.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.execute.return_value.data = [sample_user]
            
            auth_service = AuthService()
            user_data = UserCreate(
                email=sample_user["email"],
                username="newuser",
                password="password123"
            )
            
            with pytest.raises(ValueError, match="already registered"):
                await auth_service.register_user(user_data)
    
    @pytest.mark.asyncio
    async def test_password_hashing(self, mock_db):
        """Test that passwords are properly hashed."""
        from app.services.auth_service import AuthService
        from app.schemas.user import UserCreate
        
        with patch('app.services.auth_service.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.execute.return_value.data = []
            
            captured_hash = None
            def capture_insert(data):
                nonlocal captured_hash
                captured_hash = data["hashed_password"]
                return MagicMock(data=[{**data, "id": "new-user"}])
            
            mock_db.table.return_value.insert.return_value.execute.side_effect = capture_insert
            
            auth_service = AuthService()
            user_data = UserCreate(
                email="test@example.com",
                username="testuser",
                password="plainpassword"
            )
            
            await auth_service.register_user(user_data)
            
            assert captured_hash is not None
            assert captured_hash != "plainpassword"
            assert bcrypt.checkpw("plainpassword".encode(), captured_hash.encode())


class TestChatService:
    """Tests for ChatService business logic."""
    
    @pytest.mark.asyncio
    async def test_create_one_to_one_chat(self, mock_db):
        """Test creating one-to-one chat room."""
        from app.services.chat_service import ChatService
        from app.schemas.message import ChatRoomCreate
        
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock no existing room
            mock_db.table.return_value.select.return_value.execute.return_value.data = []
            
            # Mock room creation
            mock_db.table.return_value.insert.return_value.execute.return_value.data = [{
                "id": "new-room-id",
                "name": None,
                "is_group": False,
                "created_by": "creator-id",
                "created_at": "2024-01-01T00:00:00"
            }]
            
            chat_service = ChatService()
            room_data = ChatRoomCreate(
                name=None,
                is_group=False,
                participant_ids=["other-user-id"]
            )
            
            result = await chat_service.create_chat_room(room_data, "creator-id")
            
            assert result.id == "new-room-id"
            assert result.is_group is False
    
    @pytest.mark.asyncio
    async def test_save_message_with_sentiment(self, mock_db):
        """Test saving message with sentiment analysis."""
        from app.services.chat_service import ChatService
        from app.schemas.message import MessageCreate, MessageType
        
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock user is participant
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"id": "participant-id"}
            ]
            
            # Mock message save
            mock_db.table.return_value.insert.return_value.execute.return_value.data = [{
                "id": "new-msg-id",
                "content": "Great work!",
                "chat_room_id": "room-id",
                "sender_id": "user-id",
                "message_type": "text",
                "sentiment": "positive",
                "created_at": "2024-01-01T00:00:00"
            }]
            
            chat_service = ChatService()
            message_data = MessageCreate(
                content="Great work!",
                chat_room_id="room-id",
                message_type=MessageType.TEXT
            )
            
            result = await chat_service.save_message(
                message_data,
                "user-id",
                "testuser",
                sentiment="positive"
            )
            
            assert result.sentiment == "positive"
            assert result.content == "Great work!"