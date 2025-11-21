# backend/app/api/chat.py
"""
Chat API endpoints for managing rooms and messages.
Time Complexity: O(1) to O(n) depending on operation
Space Complexity: O(n) for list operations
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from ..schemas.message import (
    MessageCreate, MessageResponse, ChatRoomCreate, 
    ChatRoomResponse
)
from ..schemas.user import UserResponse
from ..services.chat_service import chat_service
from .dependencies import get_current_active_user

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/rooms", response_model=ChatRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_room(
    room_data: ChatRoomCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Create a new chat room (one-to-one or group).
    
    Business Value: Enables users to start conversations
    """
    try:
        return await chat_service.create_chat_room(room_data, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/rooms", response_model=List[dict])
async def get_user_chats(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get all chat rooms for current user.
    
    Business Value: User's chat dashboard
    """
    return await chat_service.get_user_chats(current_user.id)


@router.get("/rooms/{room_id}/messages", response_model=List[MessageResponse])
async def get_chat_history(
    room_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[str] = Query(None, description="ISO timestamp for pagination"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get chat history for a specific room.
    
    Business Value: Access to conversation history with pagination
    """
    try:
        return await chat_service.get_chat_history(
            room_id, 
            current_user.id, 
            limit, 
            before
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/rooms/{room_id}/participants", response_model=List[dict])
async def get_room_participants(
    room_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get all participants in a chat room.
    
    Business Value: See who's in the conversation
    """
    return await chat_service.get_room_participants(room_id)


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Send a message (used as fallback if WebSocket fails).
    
    Business Value: Reliable message delivery
    """
    try:
        return await chat_service.save_message(
            message_data, 
            current_user.id,
            current_user.username
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )