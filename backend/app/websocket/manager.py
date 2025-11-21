"""
WebSocket connection manager for real-time chat.
Time Complexity:
    - connect: O(1)
    - disconnect: O(1)
    - broadcast: O(n) where n is number of connections
Space Complexity: O(n) where n is number of active connections
"""
from fastapi import WebSocket
from typing import Dict, List, Set
import json
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""
    
    def __init__(self):
        """Initialize connection storage."""
        # User ID -> List of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Chat room ID -> Set of user IDs
        self.room_participants: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept and store a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        print(f"User {user_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
            user_id: User identifier
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            
            # Remove user entry if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        print(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")
    
    def join_room(self, user_id: str, room_id: str):
        """
        Add user to a chat room.
        
        Args:
            user_id: User identifier
            room_id: Chat room identifier
        """
        if room_id not in self.room_participants:
            self.room_participants[room_id] = set()
        
        self.room_participants[room_id].add(user_id)
        print(f"User {user_id} joined room {room_id}")
    
    def leave_room(self, user_id: str, room_id: str):
        """
        Remove user from a chat room.
        
        Args:
            user_id: User identifier
            room_id: Chat room identifier
        """
        if room_id in self.room_participants:
            self.room_participants[room_id].discard(user_id)
            
            # Clean up empty rooms
            if not self.room_participants[room_id]:
                del self.room_participants[room_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        """
        Send message to a specific user (all their connections).
        
        Args:
            message: Message data dictionary
            user_id: Target user identifier
        """
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected sockets
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast_to_room(self, message: dict, room_id: str, exclude_user: str = None):
        """
        Broadcast message to all users in a room.
        
        Args:
            message: Message data dictionary
            room_id: Chat room identifier
            exclude_user: Optional user ID to exclude from broadcast
        """
        if room_id not in self.room_participants:
            return
        
        for user_id in self.room_participants[room_id]:
            if user_id != exclude_user:
                await self.send_personal_message(message, user_id)
    
    async def broadcast_to_all(self, message: dict):
        """
        Broadcast message to all connected users.
        
        Args:
            message: Message data dictionary
        """
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)
    
    def get_room_participants(self, room_id: str) -> List[str]:
        """
        Get list of participants in a room.
        
        Args:
            room_id: Chat room identifier
            
        Returns:
            List of user IDs in the room
        """
        return list(self.room_participants.get(room_id, set()))
    
    def is_user_online(self, user_id: str) -> bool:
        """
        Check if user is currently connected.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user has active connections
        """
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# Singleton instance
manager = ConnectionManager()