"""
Long-Term Memory

Persistent memory for user preferences, past interactions,
and semantic search over conversation history.

Uses vector database (Pinecone) for semantic retrieval.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class UserContext:
    """Persistent context for a user."""
    user_id: str
    preferences: dict
    interaction_summary: str
    common_issues: list[str]
    policy_change_history: list[dict]
    last_updated: datetime


@dataclass
class MemoryEntry:
    """A single entry in long-term memory."""
    id: str
    user_id: str
    content: str
    embedding: list[float] | None
    metadata: dict
    created_at: datetime


class LongTermMemory:
    """
    Long-term memory with semantic search.
    
    Features:
    - Persistent storage of user preferences
    - Vector embeddings for semantic search
    - Retrieval of relevant past interactions
    """
    
    def __init__(self):
        """Initialize long-term memory."""
        # In production, connect to Pinecone/Weaviate
        self._user_contexts: dict[str, UserContext] = {}
        self._entries: list[MemoryEntry] = []
    
    async def get_user_context(self, user_id: str) -> dict:
        """
        Get persistent context for a user.
        
        Includes preferences, common issues, and interaction history.
        """
        if user_id in self._user_contexts:
            ctx = self._user_contexts[user_id]
            return {
                "preferences": ctx.preferences,
                "interaction_summary": ctx.interaction_summary,
                "common_issues": ctx.common_issues
            }
        
        # Return defaults for new user
        return {
            "preferences": {},
            "interaction_summary": "",
            "common_issues": []
        }
    
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: dict
    ) -> None:
        """Update user preferences."""
        if user_id in self._user_contexts:
            self._user_contexts[user_id].preferences.update(preferences)
            self._user_contexts[user_id].last_updated = datetime.utcnow()
        else:
            self._user_contexts[user_id] = UserContext(
                user_id=user_id,
                preferences=preferences,
                interaction_summary="",
                common_issues=[],
                policy_change_history=[],
                last_updated=datetime.utcnow()
            )
        
        logger.debug(
            "Updated user preferences",
            user_id=user_id,
            preference_count=len(preferences)
        )
    
    async def store_interaction(
        self,
        user_id: str,
        interaction: str,
        metadata: dict | None = None
    ) -> None:
        """
        Store an interaction in long-term memory.
        
        Creates an embedding for semantic search.
        """
        # In production:
        # 1. Create embedding using text-embedding model
        # 2. Store in Pinecone with metadata
        
        entry = MemoryEntry(
            id=f"{user_id}_{datetime.utcnow().timestamp()}",
            user_id=user_id,
            content=interaction,
            embedding=None,  # Would be generated
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        
        self._entries.append(entry)
        
        logger.debug(
            "Stored interaction",
            user_id=user_id,
            content_length=len(interaction)
        )
    
    async def search_similar(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> list[MemoryEntry]:
        """
        Search for similar past interactions.
        
        Uses semantic similarity via vector search.
        """
        # In production:
        # 1. Create query embedding
        # 2. Search Pinecone for similar vectors
        # 3. Filter by user_id
        # 4. Return top matches
        
        # For now, simple text matching
        user_entries = [
            e for e in self._entries
            if e.user_id == user_id
        ]
        
        # Simple keyword matching (replace with vector search)
        query_words = set(query.lower().split())
        scored = []
        
        for entry in user_entries:
            entry_words = set(entry.content.lower().split())
            overlap = len(query_words & entry_words)
            if overlap > 0:
                scored.append((entry, overlap))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [entry for entry, score in scored[:limit]]
    
    async def get_policy_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> list[dict]:
        """Get history of policy changes for a user."""
        if user_id in self._user_contexts:
            return self._user_contexts[user_id].policy_change_history[-limit:]
        return []
    
    async def record_policy_change(
        self,
        user_id: str,
        change: dict
    ) -> None:
        """Record a policy change for the user."""
        if user_id not in self._user_contexts:
            self._user_contexts[user_id] = UserContext(
                user_id=user_id,
                preferences={},
                interaction_summary="",
                common_issues=[],
                policy_change_history=[],
                last_updated=datetime.utcnow()
            )
        
        change["timestamp"] = datetime.utcnow().isoformat()
        self._user_contexts[user_id].policy_change_history.append(change)
        
        # Keep only last 50 changes
        if len(self._user_contexts[user_id].policy_change_history) > 50:
            self._user_contexts[user_id].policy_change_history = \
                self._user_contexts[user_id].policy_change_history[-50:]
    
    async def update_interaction_summary(
        self,
        user_id: str,
        summary: str
    ) -> None:
        """
        Update the running summary of user interactions.
        
        This is periodically generated by the AI to capture
        key information about the user's behavior and needs.
        """
        if user_id in self._user_contexts:
            self._user_contexts[user_id].interaction_summary = summary
            self._user_contexts[user_id].last_updated = datetime.utcnow()
        else:
            self._user_contexts[user_id] = UserContext(
                user_id=user_id,
                preferences={},
                interaction_summary=summary,
                common_issues=[],
                policy_change_history=[],
                last_updated=datetime.utcnow()
            )
