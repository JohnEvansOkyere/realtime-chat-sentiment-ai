#  backend/app/schemas/message.py


"""
Pydantic schemas for message-related requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    content: str = Field(..., min_length=1, max_length=5000)
    chat_room_id: str
    message_type: MessageType = MessageType.TEXT


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: str
    content: str
    chat_room_id: str
    sender_id: str
    sender_username: str
    message_type: MessageType
    sentiment: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatRoomCreate(BaseModel):
    """Schema for creating a chat room."""
    name: Optional[str] = Field(None, max_length=100)
    is_group: bool = False
    participant_ids: list[str] = Field(..., min_items=1)


class ChatRoomResponse(BaseModel):
    """Schema for chat room response."""
    id: str
    name: Optional[str]
    is_group: bool
    created_by: str
    created_at: datetime
    participants_count: int
    
    class Config:
        from_attributes = True