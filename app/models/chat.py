from datetime import datetime
from typing import List, Optional
from beanie import Document, Link
from pydantic import Field

class Message(Document):
    chat_id: str
    content: str
    type: str = Field(..., description="'question' or 'answer'")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "messages"
        indexes = [
            [("chat_id", 1)],
            [("created_at", -1)]
        ]

    def to_response_dict(self):
        """Convert to a response-friendly dictionary."""
        return {
            "id": str(self.id),
            "chat_id": self.chat_id,
            "content": self.content,
            "type": self.type,
            "created_at": self.created_at
        }

class ChatSession(Document):
    title: str
    document_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[Link[Message]] = Field(default_factory=list)
    is_active: bool = True

    async def to_response_dict(self):
        """Convert to a response-friendly dictionary."""
        # Fetch all messages for this chat
        messages = await Message.find(
            Message.chat_id == str(self.id)
        ).sort(Message.created_at).to_list()
        
        return {
            "id": str(self.id),  # Convert ObjectId to string
            "title": self.title,
            "document_name": self.document_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
            "messages": [msg.to_response_dict() for msg in messages]
        }

    class Settings:
        name = "chat_sessions"
        indexes = [
            [("created_at", -1)],
            [("updated_at", -1)],
            [("is_active", 1)]
        ]

    async def add_message(self, content: str, msg_type: str) -> Message:
        """Add a new message to the chat session."""
        message = Message(
            chat_id=str(self.id),
            content=content,
            type=msg_type
        )
        await message.insert()
        
        self.messages.append(Link(message, Message))
        self.updated_at = datetime.utcnow()
        await self.save()
        
        return message

    async def get_recent_messages(self, limit: int = 5) -> List[Message]:
        """Get the most recent messages for context."""
        return await Message.find(
            Message.chat_id == str(self.id)
        ).sort(-Message.created_at).limit(limit).to_list()

    @classmethod
    async def get_active_chats(cls) -> List["ChatSession"]:
        """Get all active chat sessions."""
        return await cls.find(
            cls.is_active == True
        ).sort(-cls.updated_at).to_list()

    async def delete_chat(self):
        """Soft delete the chat session."""
        self.is_active = False
        await self.save()
        
    def format_chat_history(self, messages: List[Message]) -> str:
        """Format recent messages for context."""
        formatted = []
        for msg in messages:
            role = "User" if msg.type == "question" else "Assistant"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)
