# backend/app/api/websocket.py
"""
WebSocket endpoint for real-time chat with message persistence.
Time Complexity: O(n) per message where n is room participants
Space Complexity: O(1) per connection
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
from datetime import datetime
from ..websocket.manager import manager
from ..core.security import security_service
from ..services.chat_service import chat_service
from ..schemas.message import MessageCreate, MessageType

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time chat with message persistence.
    
    Args:
        websocket: WebSocket connection
        room_id: Chat room identifier
        token: JWT token for authentication
    
    Business Value: Real-time communication with persistent storage
    """
    # Verify token
    payload = security_service.decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = payload.get('sub')
    email = payload.get('email')
    if not user_id:
        await websocket.close(code=4001, reason="Invalid user")
        return
    
    # Get username from token or query
    # In production, fetch from database
    username = email.split('@')[0]  # Simplified for now
    
    # Connect user
    await manager.connect(websocket, user_id)
    manager.join_room(user_id, room_id)
    
    # Notify room of new user
    await manager.broadcast_to_room(
        {
            "type": "user_joined",
            "user_id": user_id,
            "username": username,
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
            
            # Create message object for persistence
            message_create = MessageCreate(
                content=message_data.get('content', ''),
                chat_room_id=room_id,
                message_type=MessageType(message_data.get('message_type', 'text'))
            )
            
            # Save message to database (without ML for now, will add in Day 3)
            try:
                saved_message = await chat_service.save_message(
                    message_create,
                    user_id,
                    username
                )
                
                # Broadcast saved message to room
                message_response = {
                    "type": "message",
                    "id": saved_message.id,
                    "content": saved_message.content,
                    "sender_id": saved_message.sender_id,
                    "sender_username": saved_message.sender_username,
                    "message_type": saved_message.message_type.value,
                    "room_id": room_id,
                    "timestamp": saved_message.created_at,
                    "sentiment": saved_message.sentiment,
                    "category": saved_message.category
                }
                
                await manager.broadcast_to_room(message_response, room_id)
                
                print(f"Message saved and broadcast in room {room_id}: {saved_message.id}")
                
            except ValueError as e:
                # Send error to sender only
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    user_id
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        manager.leave_room(user_id, room_id)
        
        # Notify room of user leaving
        await manager.broadcast_to_room(
            {
                "type": "user_left",
                "user_id": user_id,
                "username": username,
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            room_id
        )
        print(f"User {username} disconnected from room {room_id}")
    
    except Exception as e:
        print(f"WebSocket error for user {user_id} in room {room_id}: {e}")
        manager.disconnect(websocket, user_id)
        manager.leave_room(user_id, room_id)