# backend/app/api/websocket.py
"""
WebSocket endpoint for real-time chat with ML sentiment analysis.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
from datetime import datetime
from ..websocket.manager import manager
from ..core.security import security_service
from ..services.chat_service import chat_service
from ..ml.inference import ml_inference_service
from ..schemas.message import MessageCreate, MessageType

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint with real-time sentiment analysis.
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
    
    username = email.split('@')[0]
    
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
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Analyze sentiment using YOUR model
            sentiment_result = ml_inference_service.analyze_sentiment(
                message_data.get('content', '')
            )
            
            # Create message object
            message_create = MessageCreate(
                content=message_data.get('content', ''),
                chat_room_id=room_id,
                message_type=MessageType(message_data.get('message_type', 'text'))
            )
            
            # Save message with sentiment
            try:
                saved_message = await chat_service.save_message(
                    message_create,
                    user_id,
                    username,
                    sentiment=sentiment_result['label'],
                    category=None  # We'll add this later if needed
                )
                
                # Broadcast message with sentiment
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
                    "sentiment_score": sentiment_result['score']
                }
                
                await manager.broadcast_to_room(message_response, room_id)
                
                print(f"✓ Message [{sentiment_result['label']}]: {saved_message.content[:50]}")
                
            except ValueError as e:
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
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)
        manager.leave_room(user_id, room_id)