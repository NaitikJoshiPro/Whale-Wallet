"""
Base classes for policy rules.

All policy rules inherit from PolicyRule and implement
the evaluate() method.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.policy_engine.executor import TransactionContext


@dataclass
class PolicyContext:
    """
    Context passed to policy rules during evaluation.
    
    Contains all information needed to make a decision.
    """
    transaction: "TransactionContext"
    user_tier: str
    current_time: datetime
    
    # Historical data that rules might need
    recent_transactions: list[dict] = field(default_factory=list)
    whitelist: list[str] = field(default_factory=list)


@dataclass
class PolicyDecision:
    """
    Decision returned by a policy rule.
    
    Multiple decisions are aggregated by the executor.
    """
    # Core decision
    allowed: bool = True
    
    # Additional requirements
    require_2fa: bool = False
    delay_seconds: int | None = None
    
    # User feedback
    warnings: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    
    # Reason for decision (for audit)
    reason: str = ""
    
    @classmethod
    def allow(cls, warnings: list[str] | None = None) -> "PolicyDecision":
        """Factory for allow decision."""
        return cls(allowed=True, warnings=warnings or [])
    
    @classmethod
    def block(cls, reason: str) -> "PolicyDecision":
        """Factory for block decision."""
        return cls(allowed=False, reason=reason)
    
    @classmethod
    def delay(cls, seconds: int, reason: str) -> "PolicyDecision":
        """Factory for delay decision."""
        return cls(allowed=True, delay_seconds=seconds, reason=reason)
    
    @classmethod
    def require_verification(cls, action: str) -> "PolicyDecision":
        """Factory for requiring additional verification."""
        return cls(
            allowed=True,
            require_2fa=True,
            required_actions=[action]
        )


class PolicyRule(ABC):
    """
    Base class for all policy rules.
    
    Each rule type implements its own evaluation logic.
    Rules are stateless - all state comes from the context.
    """
    
    def __init__(
        self,
        name: str,
        config: dict[str, Any],
        priority: int = 0
    ):
        """
        Initialize a policy rule.
        
        Args:
            name: Human-readable name for the rule
            config: Rule-specific configuration
            priority: Evaluation priority (higher = first)
        """
        self.name = name
        self.config = config
        self.priority = priority
    
    @abstractmethod
    async def evaluate(self, context: PolicyContext) -> PolicyDecision:
        """
        Evaluate the transaction against this rule.
        
        Args:
            context: Policy evaluation context
            
        Returns:
            PolicyDecision with the rule's verdict
        """
        pass
    
    def validate_config(self) -> list[str]:
        """
        Validate the rule configuration.
        
        Returns list of validation errors (empty if valid).
        Override in subclasses for specific validation.
        """
        return []
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, priority={self.priority})"
