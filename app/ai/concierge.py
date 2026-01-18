"""
AI Concierge Service

The main AI service that orchestrates agents, memory, and tools
to provide intelligent assistance to Whale Wallet users.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator
from uuid import UUID, uuid4

import structlog
from anthropic import AsyncAnthropic

from app.config import get_settings
from app.ai.agents.router import AgentRouter
from app.ai.memory.short_term import ShortTermMemory
from app.ai.memory.long_term import LongTermMemory
from app.ai.prompts.system import build_system_prompt
from app.ai.tools import AVAILABLE_TOOLS

logger = structlog.get_logger(__name__)


@dataclass
class ConversationMessage:
    """A message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: dict | None = None


@dataclass 
class ConversationState:
    """State of an active conversation."""
    id: UUID
    user_id: str
    user_tier: str
    messages: list[ConversationMessage]
    context: dict
    created_at: datetime
    last_activity: datetime


class ConciergeService:
    """
    Main AI Concierge orchestration service.
    
    Responsibilities:
    - Manage conversation state
    - Route to appropriate agents
    - Coordinate memory systems
    - Handle tool execution
    - Stream responses
    """
    
    def __init__(self):
        """Initialize the concierge service."""
        self.settings = get_settings()
        self.router = AgentRouter()
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        
        # Initialize LLM client
        self.client = AsyncAnthropic(
            api_key=self.settings.llm_api_key.get_secret_value()
        )
        
        # Active conversations (in production, use Redis)
        self._conversations: dict[UUID, ConversationState] = {}
    
    async def process_message(
        self,
        user_id: str,
        user_tier: str,
        message: str,
        conversation_id: UUID | None = None,
        context: dict | None = None
    ) -> tuple[UUID, str]:
        """
        Process a user message and return response.
        
        Args:
            user_id: User identifier
            user_tier: Membership tier
            message: User's message
            conversation_id: Existing conversation ID, or None for new
            context: Additional context (current screen, wallet state, etc.)
        
        Returns:
            Tuple of (conversation_id, response_text)
        """
        # Get or create conversation
        conv = await self._get_or_create_conversation(
            user_id, user_tier, conversation_id, context
        )
        
        # Add user message
        conv.messages.append(ConversationMessage(
            role="user",
            content=message,
            timestamp=datetime.utcnow()
        ))
        conv.last_activity = datetime.utcnow()
        
        # Build messages for LLM
        messages = self._build_llm_messages(conv)
        
        # Build system prompt with context
        system_prompt = build_system_prompt(
            user_tier=user_tier,
            active_policies=[],  # Would fetch from DB
            context=conv.context
        )
        
        logger.info(
            "Processing concierge message",
            user_id=user_id,
            conversation_id=str(conv.id),
            message_count=len(conv.messages)
        )
        
        try:
            # Call LLM
            response = await self.client.messages.create(
                model=self.settings.llm_model,
                max_tokens=2048,
                system=system_prompt,
                messages=messages,
                tools=self._format_tools_for_claude()
            )
            
            # Extract response text
            response_text = self._extract_response(response)
            
            # Add assistant message
            conv.messages.append(ConversationMessage(
                role="assistant",
                content=response_text,
                timestamp=datetime.utcnow(),
                metadata={"model": self.settings.llm_model}
            ))
            
            # Update memory
            await self.short_term.update(conv.id, conv.messages[-2:])
            
            return conv.id, response_text
            
        except Exception as e:
            logger.error(
                "LLM request failed",
                error=str(e),
                conversation_id=str(conv.id)
            )
            return conv.id, "I apologize, but I encountered an error processing your request. Please try again."
    
    async def stream_message(
        self,
        user_id: str,
        user_tier: str,
        message: str,
        conversation_id: UUID | None = None,
        context: dict | None = None
    ) -> AsyncIterator[str]:
        """
        Process a user message and stream the response.
        
        Yields chunks of the response as they're generated.
        """
        # Get or create conversation
        conv = await self._get_or_create_conversation(
            user_id, user_tier, conversation_id, context
        )
        
        # Add user message
        conv.messages.append(ConversationMessage(
            role="user",
            content=message,
            timestamp=datetime.utcnow()
        ))
        
        # Build messages and system prompt
        messages = self._build_llm_messages(conv)
        system_prompt = build_system_prompt(
            user_tier=user_tier,
            active_policies=[],
            context=conv.context
        )
        
        logger.info(
            "Streaming concierge response",
            user_id=user_id,
            conversation_id=str(conv.id)
        )
        
        full_response = []
        
        try:
            async with self.client.messages.stream(
                model=self.settings.llm_model,
                max_tokens=2048,
                system=system_prompt,
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    full_response.append(text)
                    yield text
            
            # Save complete response
            conv.messages.append(ConversationMessage(
                role="assistant",
                content="".join(full_response),
                timestamp=datetime.utcnow()
            ))
            
        except Exception as e:
            logger.error("Streaming failed", error=str(e))
            yield "I apologize, but I encountered an error. Please try again."
    
    async def analyze_transaction(
        self,
        chain: str,
        tx_data: dict
    ) -> dict:
        """
        Analyze a transaction for risks and explanation.
        
        Returns structured analysis including:
        - Plain English summary
        - Risk assessment
        - Warnings
        - Recommendations
        """
        # Build analysis prompt
        analysis_prompt = f"""Analyze this blockchain transaction:

Chain: {chain}
Transaction Data: {tx_data}

Provide:
1. A plain English summary of what this transaction does
2. Risk level (LOW/MEDIUM/HIGH/CRITICAL)
3. Specific risks or concerns
4. Recommendations for the user

Be thorough but concise. Focus on security implications."""

        try:
            response = await self.client.messages.create(
                model=self.settings.llm_model,
                max_tokens=1024,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            return {
                "analysis": response.content[0].text,
                "model": self.settings.llm_model
            }
            
        except Exception as e:
            logger.error("Transaction analysis failed", error=str(e))
            return {"error": str(e)}
    
    async def _get_or_create_conversation(
        self,
        user_id: str,
        user_tier: str,
        conversation_id: UUID | None,
        context: dict | None
    ) -> ConversationState:
        """Get existing conversation or create new one."""
        if conversation_id and conversation_id in self._conversations:
            conv = self._conversations[conversation_id]
            if context:
                conv.context.update(context)
            return conv
        
        # Create new conversation
        new_id = conversation_id or uuid4()
        conv = ConversationState(
            id=new_id,
            user_id=user_id,
            user_tier=user_tier,
            messages=[],
            context=context or {},
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        self._conversations[new_id] = conv
        
        # Load long-term context
        user_context = await self.long_term.get_user_context(user_id)
        conv.context["user_preferences"] = user_context
        
        return conv
    
    def _build_llm_messages(
        self,
        conv: ConversationState
    ) -> list[dict]:
        """Build message list for LLM API."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in conv.messages
        ]
    
    def _format_tools_for_claude(self) -> list[dict]:
        """Format available tools for Claude API."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters
            }
            for tool in AVAILABLE_TOOLS
        ]
    
    def _extract_response(self, response) -> str:
        """Extract text response from LLM response."""
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""
