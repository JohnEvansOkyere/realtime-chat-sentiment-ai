# backend/app/services/chat_service.py
"""
Chat service handling chat rooms, messages, and participants.
Time Complexity:
    - create_chat_room: O(n) where n is number of participants
    - send_message: O(1) - single database insert
    - get_chat_history: O(m) where m is limit size
    - get_user_chats: O(k) where k is number of user's chats
Space Complexity: O(1) for operations, O(n) for query results
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.database import db_service
from ..schemas.message import (
    MessageCreate, MessageResponse, ChatRoomCreate, 
    ChatRoomResponse, MessageType
)


class ChatService:
    """Handles all chat-related operations."""
    
    def __init__(self):
        """Initialize with database service."""
        self.db = db_service.get_admin_client()
    
    async def create_chat_room(
        self, 
        room_data: ChatRoomCreate, 
        creator_id: str
    ) -> ChatRoomResponse:
        """
        Create a new chat room (one-to-one or group).
        
        Args:
            room_data: Chat room creation data
            creator_id: User creating the room
            
        Returns:
            Created chat room details
            
        Business Value: Enables organized conversations
        """
        # For one-to-one chat, check if room already exists
        if not room_data.is_group and len(room_data.participant_ids) == 1:
            existing_room = await self._find_one_to_one_room(
                creator_id, 
                room_data.participant_ids[0]
            )
            if existing_room:
                return existing_room
        
        # Create chat room
        room_dict = {
            'name': room_data.name,
            'is_group': room_data.is_group,
            'created_by': creator_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = self.db.table('chat_rooms').insert(room_dict).execute()
        
        if not result.data:
            raise ValueError("Failed to create chat room")
        
        room = result.data[0]
        
        # Add participants (including creator)
        participants = list(set([creator_id] + room_data.participant_ids))
        await self._add_participants(room['id'], participants)
        
        return ChatRoomResponse(
            id=room['id'],
            name=room['name'],
            is_group=room['is_group'],
            created_by=room['created_by'],
            created_at=room['created_at'],
            participants_count=len(participants)
        )
    
    async def _find_one_to_one_room(
        self, 
        user1_id: str, 
        user2_id: str
    ) -> Optional[ChatRoomResponse]:
        """
        Find existing one-to-one chat room between two users.
        
        Args:
            user1_id: First user ID
            user2_id: Second user ID
            
        Returns:
            Existing room or None
        """
        # Get all rooms where user1 is a participant
        user1_rooms = self.db.table('chat_participants')\
            .select('chat_room_id')\
            .eq('user_id', user1_id)\
            .execute()
        
        if not user1_rooms.data:
            return None
        
        room_ids = [r['chat_room_id'] for r in user1_rooms.data]
        
        # Get all rooms where user2 is a participant
        user2_rooms = self.db.table('chat_participants')\
            .select('chat_room_id')\
            .eq('user_id', user2_id)\
            .in_('chat_room_id', room_ids)\
            .execute()
        
        if not user2_rooms.data:
            return None
        
        # Find one-to-one rooms
        common_room_ids = [r['chat_room_id'] for r in user2_rooms.data]
        
        for room_id in common_room_ids:
            room = self.db.table('chat_rooms')\
                .select('*')\
                .eq('id', room_id)\
                .eq('is_group', False)\
                .execute()
            
            if room.data:
                room_data = room.data[0]
                # Verify it's exactly 2 participants
                participants_count = self.db.table('chat_participants')\
                    .select('id', count='exact')\
                    .eq('chat_room_id', room_id)\
                    .execute()
                
                if participants_count.count == 2:
                    return ChatRoomResponse(
                        id=room_data['id'],
                        name=room_data['name'],
                        is_group=room_data['is_group'],
                        created_by=room_data['created_by'],
                        created_at=room_data['created_at'],
                        participants_count=2
                    )
        
        return None
    
    async def _add_participants(self, room_id: str, user_ids: List[str]):
        """
        Add participants to a chat room.
        
        Args:
            room_id: Chat room ID
            user_ids: List of user IDs to add
        """
        participants = [
            {
                'chat_room_id': room_id,
                'user_id': user_id,
                'joined_at': datetime.utcnow().isoformat()
            }
            for user_id in user_ids
        ]
        
        self.db.table('chat_participants').insert(participants).execute()
    
    async def save_message(
        self, 
        message_data: MessageCreate, 
        sender_id: str,
        sender_username: str,
        sentiment: Optional[str] = None,
        category: Optional[str] = None
    ) -> MessageResponse:
        """
        Save a message to database.
        
        Args:
            message_data: Message content and metadata
            sender_id: User sending the message
            sender_username: Username of sender
            sentiment: Optional AI-detected sentiment
            category: Optional AI-detected category
            
        Returns:
            Saved message details
            
        Business Value: Persistent chat history with AI insights
        """
        # Verify user is participant
        participant = self.db.table('chat_participants')\
            .select('id')\
            .eq('chat_room_id', message_data.chat_room_id)\
            .eq('user_id', sender_id)\
            .execute()
        
        if not participant.data:
            raise ValueError("User is not a participant of this chat room")
        
        # Save message
        message_dict = {
            'content': message_data.content,
            'chat_room_id': message_data.chat_room_id,
            'sender_id': sender_id,
            'message_type': message_data.message_type.value,
            'sentiment': sentiment,
            'category': category,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = self.db.table('messages').insert(message_dict).execute()
        
        if not result.data:
            raise ValueError("Failed to save message")
        
        message = result.data[0]
        
        return MessageResponse(
            id=message['id'],
            content=message['content'],
            chat_room_id=message['chat_room_id'],
            sender_id=message['sender_id'],
            sender_username=sender_username,
            message_type=MessageType(message['message_type']),
            sentiment=message.get('sentiment'),
            category=message.get('category'),
            created_at=message['created_at']
        )
    
    async def get_chat_history(
        self, 
        room_id: str, 
        user_id: str,
        limit: int = 50,
        before_timestamp: Optional[str] = None
    ) -> List[MessageResponse]:
        """
        Get chat history for a room.
        
        Args:
            room_id: Chat room ID
            user_id: User requesting history
            limit: Number of messages to retrieve
            before_timestamp: Get messages before this timestamp (pagination)
            
        Returns:
            List of messages
            
        Business Value: Access to conversation history
        """
        # Verify user is participant
        participant = self.db.table('chat_participants')\
            .select('id')\
            .eq('chat_room_id', room_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if not participant.data:
            raise ValueError("User is not a participant of this chat room")
        
        # Build query
        query = self.db.table('messages')\
            .select('*, users!messages_sender_id_fkey(username)')\
            .eq('chat_room_id', room_id)\
            .order('created_at', desc=True)\
            .limit(limit)
        
        if before_timestamp:
            query = query.lt('created_at', before_timestamp)
        
        result = query.execute()
        
        messages = []
        for msg in result.data:
            messages.append(MessageResponse(
                id=msg['id'],
                content=msg['content'],
                chat_room_id=msg['chat_room_id'],
                sender_id=msg['sender_id'],
                sender_username=msg['users']['username'],
                message_type=MessageType(msg['message_type']),
                sentiment=msg.get('sentiment'),
                category=msg.get('category'),
                created_at=msg['created_at']
            ))
        
        # Reverse to get chronological order
        return list(reversed(messages))
    
    async def get_user_chats(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all chat rooms for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of chat rooms with metadata
            
        Business Value: User's chat dashboard
        """
        # Get user's chat room IDs
        participations = self.db.table('chat_participants')\
            .select('chat_room_id, joined_at')\
            .eq('user_id', user_id)\
            .execute()
        
        if not participations.data:
            return []
        
        room_ids = [p['chat_room_id'] for p in participations.data]
        
        # Get room details
        rooms = self.db.table('chat_rooms')\
            .select('*')\
            .in_('id', room_ids)\
            .execute()
        
        result = []
        for room in rooms.data:
            # Get participant count
            participants = self.db.table('chat_participants')\
                .select('id', count='exact')\
                .eq('chat_room_id', room['id'])\
                .execute()
            
            # Get last message
            last_message = self.db.table('messages')\
                .select('content, created_at')\
                .eq('chat_room_id', room['id'])\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            # For one-to-one chats, get other user's name
            display_name = room['name']
            if not room['is_group']:
                other_participants = self.db.table('chat_participants')\
                    .select('users!chat_participants_user_id_fkey(username, full_name)')\
                    .eq('chat_room_id', room['id'])\
                    .neq('user_id', user_id)\
                    .execute()
                
                if other_participants.data:
                    other_user = other_participants.data[0]['users']
                    display_name = other_user.get('full_name') or other_user['username']
            
            result.append({
                'id': room['id'],
                'name': display_name,
                'is_group': room['is_group'],
                'participants_count': participants.count,
                'last_message': last_message.data[0] if last_message.data else None,
                'created_at': room['created_at']
            })
        
        return result
    
    async def get_room_participants(self, room_id: str) -> List[Dict[str, Any]]:
        """
        Get all participants in a chat room.
        
        Args:
            room_id: Chat room ID
            
        Returns:
            List of participants with user details
        """
        participants = self.db.table('chat_participants')\
            .select('users!chat_participants_user_id_fkey(id, username, full_name, email)')\
            .eq('chat_room_id', room_id)\
            .execute()
        
        return [p['users'] for p in participants.data]


# Singleton instance
chat_service = ChatService()