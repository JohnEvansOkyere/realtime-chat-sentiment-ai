"""
WebSocket endpoint for real-time chat.
Time Complexity: O(n) per message where n is room participants
Space Complexity: O(1) per connection
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import json
from datetime import datetime
from ..websocket.manager import manager
from ..core.security import security_service

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time chat in a specific room.
    
    Args:
        websocket: WebSocket connection
        room_id: Chat room identifier
        token: JWT token for authentication
    
    Business Value: Enables real-time bidirectional communication
    """
    # Verify token
    payload = security_service.decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = payload.get('sub')
    if not user_id:
        await websocket.close(code=4001, reason="Invalid user")
        return
    
    # Connect user
    await manager.connect(websocket, user_id)
    manager.join_room(user_id, room_id)
    
    # Notify room of new user
    await manager.broadcast_to_room(
        {
            "type": "user_joined",
            "user_id": user_id,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat()
        },
        room_id,
        exclude_user=user_id
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Add metadata
            message_data["sender_id"] = user_id
            message_data["room_id"] = room_id
            message_data["timestamp"] = datetime.utcnow().isoformat()
            
            # Broadcast to room (this will be enhanced with ML in Day 3)
            await manager.broadcast_to_room(message_data, room_id)
            
            print(f"Message in room {room_id} from user {user_id}: {message_data.get('content', '')[:50]}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        manager.leave_room(user_id, room_id)
        
        # Notify room of user leaving
        await manager.broadcast_to_room(
            {
                "type": "user_left",
                "user_id": user_id,
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            room_id
        )
        print(f"User {user_id} disconnected from room {room_id}")
    
    except Exception as e:
        print(f"WebSocket error for user {user_id} in room {room_id}: {e}")
        manager.disconnect(websocket, user_id)
        manager.leave_room(user_id, room_id)