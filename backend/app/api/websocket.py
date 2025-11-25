# backend/app/api/websocket.py
"""
WebSocket endpoint for real-time chat with ML sentiment analysis.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
import asyncio
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
    WebSocket endpoint with real-time sentiment analysis and heartbeat.
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
    
    # Check if user already connected to this room (prevent duplicates)
    existing_connection = manager.is_user_in_room(user_id, room_id)
    
    # Connect user
    await manager.connect(websocket, user_id)
    manager.join_room(user_id, room_id)
    
    # Only notify if this is a NEW connection (not reconnect)
    if not existing_connection:
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
        print(f"✅ {username} joined room {room_id}")
    else:
        print(f"🔄 {username} reconnected to room {room_id}")
    
    # Heartbeat task to keep connection alive
    async def heartbeat():
        try:
            while True:
                await asyncio.sleep(30)  # Send ping every 30 seconds
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
        except asyncio.CancelledError:
            pass
    
    heartbeat_task = asyncio.create_task(heartbeat())
    
    try:
        while True:
            # Receive message with timeout
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            except asyncio.TimeoutError:
                # Connection idle for too long
                print(f"⚠️ Connection timeout for {username}")
                break
            
            message_data = json.loads(data)
            
            # Handle pong response (heartbeat)
            if message_data.get('type') == 'pong':
                continue
            
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
                    category=None
                )
                
                # Convert datetime to ISO string for JSON serialization
                timestamp = saved_message.created_at
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.isoformat()
                elif isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).isoformat()
                    except:
                        timestamp = timestamp
                
                # Broadcast message with sentiment
                message_response = {
                    "type": "message",
                    "id": saved_message.id,
                    "content": saved_message.content,
                    "sender_id": saved_message.sender_id,
                    "sender_username": saved_message.sender_username,
                    "message_type": saved_message.message_type.value,
                    "room_id": room_id,
                    "created_at": timestamp,
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
        pass
    except Exception as e:
        print(f"WebSocket error for {username}: {e}")
    finally:
        # Cancel heartbeat
        heartbeat_task.cancel()
        
        # Disconnect and notify
        manager.disconnect(websocket, user_id)
        manager.leave_room(user_id, room_id)
        
        # Only notify if user is NOT connected elsewhere
        if not manager.is_user_online(user_id):
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
            print(f"❌ {username} left room {room_id}")