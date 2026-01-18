"""
Agent Router

Routes user requests to the appropriate specialist agent
based on intent classification.
"""

from enum import Enum
from typing import Callable

import structlog

logger = structlog.get_logger(__name__)


class AgentType(str, Enum):
    """Types of specialist agents."""
    SUPPORT = "support"      # Technical help
    ANALYST = "analyst"      # Transaction analysis
    ADVISOR = "advisor"      # Strategy/policy advice
    SECURITY = "security"    # Threat assessment


class AgentRouter:
    """
    Routes requests to appropriate specialist agents.
    
    Uses intent classification to determine which agent
    should handle the request.
    """
    
    def __init__(self):
        """Initialize router with intent patterns."""
        # Intent patterns (in production, use ML classifier)
        self.intent_patterns = {
            AgentType.SUPPORT: [
                "how do i", "how to", "help", "error", "can't",
                "doesn't work", "problem", "issue", "tutorial"
            ],
            AgentType.ANALYST: [
                "what is this", "analyze", "transaction", "contract",
                "explain", "what does", "safe to"
            ],
            AgentType.ADVISOR: [
                "should i", "recommend", "best", "strategy",
                "policy", "limit", "inheritance", "settings"
            ],
            AgentType.SECURITY: [
                "scam", "hack", "stolen", "suspicious", "phishing",
                "malicious", "risk", "danger", "duress"
            ]
        }
    
    def classify_intent(self, message: str) -> AgentType:
        """
        Classify the intent of a user message.
        
        Returns the most appropriate agent type.
        """
        message_lower = message.lower()
        
        # Score each agent type
        scores = {}
        for agent_type, patterns in self.intent_patterns.items():
            score = sum(1 for p in patterns if p in message_lower)
            scores[agent_type] = score
        
        # Return highest scoring, default to SUPPORT
        best_type = max(scores.items(), key=lambda x: x[1])
        
        if best_type[1] == 0:
            return AgentType.SUPPORT
        
        logger.debug(
            "Intent classified",
            agent_type=best_type[0].value,
            score=best_type[1]
        )
        
        return best_type[0]
    
    def get_agent_system_prompt_modifier(
        self,
        agent_type: AgentType
    ) -> str:
        """
        Get additional system prompt instructions for the agent type.
        """
        modifiers = {
            AgentType.SUPPORT: """
You are currently acting as a Technical Support specialist.
Focus on:
- Providing clear, step-by-step instructions
- Explaining technical concepts simply
- Troubleshooting issues
- Guiding through wallet features
""",
            AgentType.ANALYST: """
You are currently acting as a Transaction Analyst.
Focus on:
- Explaining what transactions and contracts do
- Identifying risks in blockchain interactions
- Decoding function calls and parameters
- Comparing to known patterns (swaps, approvals, etc.)
""",
            AgentType.ADVISOR: """
You are currently acting as a Wealth Strategy Advisor.
Focus on:
- Recommending security policies based on user behavior
- Suggesting best practices for asset protection
- Helping configure inheritance and recovery
- Optimizing wallet settings for user's needs
""",
            AgentType.SECURITY: """
You are currently acting as a Security Specialist.
Focus on:
- Assessing threat levels
- Identifying scam patterns
- Recommending immediate protective actions
- Explaining attack vectors and how to avoid them
IMPORTANT: If user may be in physical danger, recommend they contact local authorities.
"""
        }
        
        return modifiers.get(agent_type, "")
    
    def requires_human_escalation(
        self,
        message: str,
        agent_type: AgentType
    ) -> bool:
        """
        Determine if request should be escalated to human.
        
        Some requests are too complex or sensitive for AI.
        """
        escalation_triggers = [
            "speak to human", "talk to person", "real person",
            "legal", "lawsuit", "attorney", "police",
            "life threatening", "emergency", "kidnap"
        ]
        
        message_lower = message.lower()
        
        if any(trigger in message_lower for trigger in escalation_triggers):
            logger.warning(
                "Escalation triggered",
                reason="keyword_match"
            )
            return True
        
        return False
