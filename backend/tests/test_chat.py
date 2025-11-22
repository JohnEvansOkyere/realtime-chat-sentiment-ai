# backend/tests/test_chat.py
"""
Unit tests for chat endpoints.
Coverage: Create Room, Get Rooms, Send Message, Get Messages, Participants
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import status


class TestChatRoomCreation:
    """Tests for chat room creation."""
    
    def test_create_one_to_one_chat(self, client, auth_headers, mock_db, sample_user):
        """Test creating one-to-one chat room."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock no existing room
            mock_db.table.return_value.select.return_value.execute.return_value.data = []
            
            # Mock room creation
            mock_db.table.return_value.insert.return_value.execute.return_value.data = [{
                "id": "new-room-id",
                "name": None,
                "is_group": False,
                "created_by": sample_user["id"],
                "created_at": "2024-01-01T00:00:00"
            }]
            
            response = client.post(
                "/api/v1/chat/rooms",
                headers=auth_headers,
                json={
                    "name": None,
                    "is_group": False,
                    "participant_ids": ["other-user-id"]
                }
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["is_group"] is False
            assert data["participants_count"] >= 2
    
    def test_create_group_chat(self, client, auth_headers, mock_db, sample_user):
        """Test creating group chat room."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.insert.return_value.execute.return_value.data = [{
                "id": "new-group-id",
                "name": "Test Group",
                "is_group": True,
                "created_by": sample_user["id"],
                "created_at": "2024-01-01T00:00:00"
            }]
            
            response = client.post(
                "/api/v1/chat/rooms",
                headers=auth_headers,
                json={
                    "name": "Test Group",
                    "is_group": True,
                    "participant_ids": ["user1", "user2", "user3"]
                }
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["is_group"] is True
            assert data["name"] == "Test Group"
    
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
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetUserChats:
    """Tests for retrieving user's chat rooms."""
    
    def test_get_user_chats_success(self, client, auth_headers, mock_db):
        """Test getting user's chat rooms."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock user participations
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"chat_room_id": "room1"},
                {"chat_room_id": "room2"}
            ]
            
            # Mock room details
            mock_db.table.return_value.select.return_value.in_.return_value.execute.return_value.data = [
                {
                    "id": "room1",
                    "name": "Chat 1",
                    "is_group": False,
                    "created_at": "2024-01-01T00:00:00"
                },
                {
                    "id": "room2",
                    "name": "Chat 2",
                    "is_group": True,
                    "created_at": "2024-01-01T00:00:00"
                }
            ]
            
            # Mock participant counts
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.count = 2
            
            response = client.get(
                "/api/v1/chat/rooms",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
    
    def test_get_chats_empty_list(self, client, auth_headers, mock_db):
        """Test getting chats when user has no chats."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            response = client.get(
                "/api/v1/chat/rooms",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.json() == []


class TestGetChatHistory:
    """Tests for retrieving chat messages."""
    
    def test_get_messages_success(self, client, auth_headers, mock_db, sample_message):
        """Test getting chat history."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock user is participant
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"id": "participant-id"}
            ]
            
            # Mock messages
            mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
                {
                    **sample_message,
                    "users": {"username": "testuser"}
                }
            ]
            
            response = client.get(
                f"/api/v1/chat/rooms/{sample_message['chat_room_id']}/messages",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) >= 1
            assert data[0]["content"] == sample_message["content"]
    
    def test_get_messages_not_participant(self, client, auth_headers, mock_db):
        """Test getting messages from room user is not part of."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock user is NOT participant
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            response = client.get(
                "/api/v1/chat/rooms/some-room-id/messages",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_messages_with_limit(self, client, auth_headers, mock_db):
        """Test pagination with limit parameter."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"id": "participant-id"}
            ]
            
            response = client.get(
                "/api/v1/chat/rooms/room-id/messages?limit=10",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK


class TestGroupManagement:
    """Tests for group management features."""
    
    def test_add_participant_success(self, client, auth_headers, mock_db, sample_user):
        """Test adding participant to group."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock room exists and user is creator
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
                "id": "room-id",
                "is_group": True,
                "created_by": sample_user["id"]
            }
            
            # Mock new user exists
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
                "id": "new-user-id"
            }
            
            # Mock user not already participant
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            response = client.post(
                "/api/v1/chat/rooms/room-id/participants?user_id=new-user-id",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_201_CREATED
    
    def test_add_participant_not_creator(self, client, auth_headers, mock_db):
        """Test adding participant when not group creator."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock user is NOT creator
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
                "id": "room-id",
                "is_group": True,
                "created_by": "different-user-id"
            }
            
            response = client.post(
                "/api/v1/chat/rooms/room-id/participants?user_id=new-user-id",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_remove_participant_success(self, client, auth_headers, mock_db, sample_user):
        """Test removing participant from group."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock room exists and user is creator
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
                "id": "room-id",
                "is_group": True,
                "created_by": sample_user["id"]
            }
            
            # Mock successful delete
            mock_db.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = [
                {"id": "participant-id"}
            ]
            
            response = client.delete(
                "/api/v1/chat/rooms/room-id/participants/user-to-remove",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
    
    def test_update_group_name(self, client, auth_headers, mock_db, sample_user):
        """Test updating group chat name."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock room exists and user is creator
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
                "id": "room-id",
                "is_group": True,
                "created_by": sample_user["id"]
            }
            
            # Mock successful update
            mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
                "id": "room-id",
                "name": "New Group Name",
                "is_group": True,
                "created_by": sample_user["id"],
                "created_at": "2024-01-01T00:00:00"
            }]
            
            response = client.put(
                "/api/v1/chat/rooms/room-id?name=New Group Name",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["name"] == "New Group Name"