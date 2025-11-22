# backend/tests/test_websocket.py
"""
Unit tests for WebSocket functionality.
Coverage: Connection, Message Broadcasting, Authentication, Reconnection
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect


class TestWebSocketConnection:
    """Tests for WebSocket connection handling."""
    
    def test_websocket_connect_success(self, client, valid_access_token, mock_db, sample_user):
        """Test successful WebSocket connection."""
        with patch('app.api.websocket.db_service.get_admin_client', return_value=mock_db):
            # Mock user exists
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_user
            
            # Mock user is participant
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"id": "participant-id"}
            ]
            
            with client.websocket_connect(f"/api/v1/ws/room-id?token={valid_access_token}") as websocket:
                # Connection should be established
                assert websocket is not None
    
    def test_websocket_connect_no_token(self, client):
        """Test WebSocket connection without token."""
        with pytest.raises(Exception):
            with client.websocket_connect("/api/v1/ws/room-id"):
                pass
    
    def test_websocket_connect_invalid_token(self, client):
        """Test WebSocket connection with invalid token."""
        with pytest.raises(Exception):
            with client.websocket_connect("/api/v1/ws/room-id?token=invalid.token"):
                pass
    
    def test_websocket_not_participant(self, client, valid_access_token, mock_db, sample_user):
        """Test WebSocket connection when user is not room participant."""
        with patch('app.api.websocket.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_user
            
            # Mock user is NOT participant
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            with pytest.raises(Exception):
                with client.websocket_connect(f"/api/v1/ws/room-id?token={valid_access_token}"):
                    pass


class TestWebSocketMessaging:
    """Tests for WebSocket message handling."""
    
    def test_send_receive_message(self, client, valid_access_token, mock_db, sample_user):
        """Test sending and receiving messages via WebSocket."""
        with patch('app.api.websocket.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_user
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "participant-id"}]
            
            # Mock message save
            mock_db.table.return_value.insert.return_value.execute.return_value.data = [{
                "id": "new-msg-id",
                "content": "Test message",
                "sender_id": sample_user["id"],
                "chat_room_id": "room-id",
                "sentiment": "neutral",
                "created_at": "2024-01-01T00:00:00"
            }]
            
            with patch('app.ml.inference.ml_inference_service.analyze_sentiment', return_value={"label": "neutral", "score": 0.8}):
                with client.websocket_connect(f"/api/v1/ws/room-id?token={valid_access_token}") as websocket:
                    # Send message
                    websocket.send_json({
                        "content": "Test message",
                        "message_type": "text"
                    })
                    
                    # Receive broadcast
                    data = websocket.receive_json()
                    assert data["type"] == "message"
                    assert data["content"] == "Test message"


class TestConnectionManager:
    """Tests for WebSocket connection manager."""
    
    @pytest.mark.asyncio
    async def test_connection_manager_connect(self):
        """Test adding connection to manager."""
        from app.api.websocket import ConnectionManager
        from unittest.mock import MagicMock
        
        manager = ConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        
        await manager.connect(mock_ws, "room1", "user1", "testuser")
        
        assert "room1" in manager.active_connections
        assert "user1" in manager.active_connections["room1"]
    
    @pytest.mark.asyncio
    async def test_connection_manager_disconnect(self):
        """Test removing connection from manager."""
        from app.api.websocket import ConnectionManager
        from unittest.mock import MagicMock
        
        manager = ConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        
        await manager.connect(mock_ws, "room1", "user1", "testuser")
        await manager.disconnect(mock_ws, "room1", "user1")
        
        assert "user1" not in manager.active_connections.get("room1", {})
    
    @pytest.mark.asyncio
    async def test_connection_manager_broadcast(self):
        """Test broadcasting message to all connections."""
        from app.api.websocket import ConnectionManager
        from unittest.mock import MagicMock
        
        manager = ConnectionManager()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        mock_ws1.accept = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        mock_ws2.send_json = AsyncMock()
        
        await manager.connect(mock_ws1, "room1", "user1", "user1")
        await manager.connect(mock_ws2, "room1", "user2", "user2")
        
        message = {"type": "test", "content": "hello"}
        await manager.broadcast("room1", message)
        
        mock_ws1.send_json.assert_called_with(message)
        mock_ws2.send_json.assert_called_with(message)