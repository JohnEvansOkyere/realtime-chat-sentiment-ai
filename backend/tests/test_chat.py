# backend/tests/test_chat.py
"""
Unit tests for chat endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import status


class TestChatRoomCreation:
    """Tests for chat room creation."""
    
    # DELETE THIS TEST - it's hitting the real database
    # def test_create_one_to_one_chat(self, authenticated_client, sample_user):
    #     ...
    
    def test_create_chat_unauthorized(self, client):
        """Test creating chat room without authentication."""
        response = client.post(
            "/api/v1/chat/rooms",
            json={
                "name": "Test",
                "is_group": False,
                "participant_ids": ["user1"]
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetUserChats:
    """Tests for retrieving user's chat rooms."""
    
    def test_get_user_chats_success(self, authenticated_client):
        """Test getting user's chat rooms."""
        mock_chats = [
            {
                "id": "room1",
                "name": "Chat 1",
                "is_group": False,
                "participants_count": 2,
                "last_message": None,
                "created_at": "2024-01-01T00:00:00"
            }
        ]
        
        mock_service = MagicMock()
        mock_service.get_user_chats = AsyncMock(return_value=mock_chats)
        
        with patch('app.api.chat.chat_service', mock_service):
            response = authenticated_client.get("/api/v1/chat/rooms")
            
            assert response.status_code == status.HTTP_200_OK
            assert isinstance(response.json(), list)


class TestGetChatHistory:
    """Tests for retrieving chat messages."""
    
    # DELETE THIS TEST - it's hitting the real database
    # def test_get_messages_not_participant(self, authenticated_client):
    #     ...
    
    def test_get_messages_success(self, authenticated_client, sample_message):
        """Test getting chat history successfully."""
        from app.schemas.message import MessageResponse, MessageType
        
        mock_messages = [
            MessageResponse(
                id=sample_message["id"],
                content=sample_message["content"],
                chat_room_id=sample_message["chat_room_id"],
                sender_id=sample_message["sender_id"],
                sender_username="testuser",
                message_type=MessageType.TEXT,
                sentiment="positive",
                created_at=sample_message["created_at"]
            )
        ]
        
        mock_service = MagicMock()
        mock_service.get_chat_history = AsyncMock(return_value=mock_messages)
        
        with patch('app.api.chat.chat_service', mock_service):
            response = authenticated_client.get("/api/v1/chat/rooms/room-id/messages")
            
            assert response.status_code == status.HTTP_200_OK
            assert len(response.json()) == 1


class TestGroupManagement:
    """Tests for group management features."""
    
    def test_add_participant_not_creator(self, authenticated_client, sample_user):
        """Test adding participant when not group creator."""
        mock_room = {
            "id": "room-id",
            "is_group": True,
            "created_by": "different-user-id"
        }
        
        mock_service = MagicMock()
        mock_service.get_room_details = AsyncMock(return_value=mock_room)
        
        with patch('app.api.chat.chat_service', mock_service):
            response = authenticated_client.post("/api/v1/chat/rooms/room-id/participants?user_id=new-user-id")
            
            assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_add_participant_success(self, authenticated_client, sample_user):
        """Test adding participant as creator."""
        mock_room = {
            "id": "room-id",
            "is_group": True,
            "created_by": sample_user["id"]
        }
        
        mock_service = MagicMock()
        mock_service.get_room_details = AsyncMock(return_value=mock_room)
        mock_service.add_participant = AsyncMock(return_value=None)
        
        with patch('app.api.chat.chat_service', mock_service):
            response = authenticated_client.post("/api/v1/chat/rooms/room-id/participants?user_id=new-user-id")
            
            assert response.status_code == status.HTTP_201_CREATED