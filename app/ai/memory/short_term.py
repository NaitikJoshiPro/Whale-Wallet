"""
Short-Term Memory

Session-scoped memory for active conversations.
Stores recent messages and context for the current session.

In production, this uses Redis for distributed state.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SessionContext:
    """Context for an active session."""
    conversation_id: UUID
    messages: list[dict]
    context: dict
    created_at: datetime
    last_access: datetime
    ttl_minutes: int = 30


class ShortTermMemory:
    """
    Short-term memory for active conversations.
    
    Features:
    - In-memory storage (Redis in production)
    - Automatic expiration
    - Context summarization for long conversations
    """
    
    def __init__(self, ttl_minutes: int = 30):
        """Initialize with TTL for entries."""
        self.ttl_minutes = ttl_minutes
        self._storage: dict[UUID, SessionContext] = {}
    
    async def update(
        self,
        conversation_id: UUID,
        messages: list[Any]
    ) -> None:
        """
        Update memory with new messages.
        
        Also triggers cleanup of expired entries.
        """
        await self._cleanup_expired()
        
        if conversation_id in self._storage:
            session = self._storage[conversation_id]
            session.messages.extend([
                {"role": m.role, "content": m.content[:500]}  # Truncate
                for m in messages
            ])
            session.last_access = datetime.utcnow()
            
            # Summarize if too many messages
            if len(session.messages) > 20:
                await self._summarize_old_messages(session)
        else:
            self._storage[conversation_id] = SessionContext(
                conversation_id=conversation_id,
                messages=[
                    {"role": m.role, "content": m.content[:500]}
                    for m in messages
                ],
                context={},
                created_at=datetime.utcnow(),
                last_access=datetime.utcnow(),
                ttl_minutes=self.ttl_minutes
            )
        
        logger.debug(
            "Short-term memory updated",
            conversation_id=str(conversation_id),
            message_count=len(self._storage[conversation_id].messages)
        )
    
    async def get(self, conversation_id: UUID) -> SessionContext | None:
        """Get session context if it exists and isn't expired."""
        session = self._storage.get(conversation_id)
        
        if session:
            if self._is_expired(session):
                del self._storage[conversation_id]
                return None
            
            session.last_access = datetime.utcnow()
            return session
        
        return None
    
    async def get_recent_messages(
        self,
        conversation_id: UUID,
        count: int = 10
    ) -> list[dict]:
        """Get the most recent messages from a conversation."""
        session = await self.get(conversation_id)
        
        if session:
            return session.messages[-count:]
        
        return []
    
    async def set_context(
        self,
        conversation_id: UUID,
        key: str,
        value: Any
    ) -> None:
        """Set a context value for the session."""
        session = await self.get(conversation_id)
        
        if session:
            session.context[key] = value
    
    async def get_context(
        self,
        conversation_id: UUID,
        key: str
    ) -> Any | None:
        """Get a context value from the session."""
        session = await self.get(conversation_id)
        
        if session:
            return session.context.get(key)
        
        return None
    
    async def delete(self, conversation_id: UUID) -> None:
        """Delete a conversation from memory."""
        if conversation_id in self._storage:
            del self._storage[conversation_id]
    
    async def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        expired = [
            cid for cid, session in self._storage.items()
            if self._is_expired(session)
        ]
        
        for cid in expired:
            del self._storage[cid]
        
        if expired:
            logger.debug("Cleaned up expired sessions", count=len(expired))
    
    def _is_expired(self, session: SessionContext) -> bool:
        """Check if a session is expired."""
        expiry = session.last_access + timedelta(minutes=session.ttl_minutes)
        return datetime.utcnow() > expiry
    
    async def _summarize_old_messages(self, session: SessionContext) -> None:
        """
        Summarize old messages to save context window.
        
        Keeps the last 10 messages intact and summarizes older ones.
        In production, this would call the LLM to generate a summary.
        """
        if len(session.messages) <= 10:
            return
        
        old_messages = session.messages[:-10]
        recent_messages = session.messages[-10:]
        
        # In production: call LLM to summarize old_messages
        summary = f"[Previous {len(old_messages)} messages summarized]"
        
        session.messages = [
            {"role": "system", "content": summary}
        ] + recent_messages
        
        logger.debug(
            "Summarized old messages",
            conversation_id=str(session.conversation_id),
            summarized_count=len(old_messages)
        )
