"""
Policy Executor

Core policy execution engine. Evaluates transactions against
all configured policies and returns a decision.

This code is designed to run inside a TEE (Trusted Execution Environment)
where it cannot be tampered with, even by the wallet administrators.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Protocol, Any

import structlog

from app.policy_engine.rules.base import PolicyRule, PolicyContext, PolicyDecision

logger = structlog.get_logger(__name__)


class DecisionType(str, Enum):
    """Final policy decision types."""
    ALLOW = "allow"
    BLOCK = "block"
    DELAY = "delay"
    REQUIRE_2FA = "require_2fa"
    WARN = "warn"


@dataclass
class ExecutionResult:
    """Result of policy execution."""
    decision: DecisionType
    
    # Details
    blocking_rule: str | None = None
    delay_seconds: int | None = None
    warnings: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    
    # Audit trail
    rules_evaluated: list[str] = field(default_factory=list)
    evaluation_time_ms: float = 0
    
    def __post_init__(self):
        """Ensure consistency."""
        if self.decision == DecisionType.DELAY and not self.delay_seconds:
            self.delay_seconds = 86400  # Default 24 hours


@dataclass
class TransactionContext:
    """
    Context about the transaction being evaluated.
    
    This is the "input" to the policy engine.
    """
    # Transaction details
    chain: str
    to_address: str
    value_native: Decimal
    value_usd: Decimal
    data: bytes | None = None
    
    # User context
    user_id: str = ""
    user_tier: str = "orca"
    
    # Historical context
    daily_outflow_usd: Decimal = Decimal("0")
    is_new_address: bool = True
    address_in_whitelist: bool = False
    
    # Environment
    current_time: datetime = field(default_factory=datetime.utcnow)
    user_timezone: str = "UTC"
    
    # Security flags
    duress_mode_active: bool = False
    biometric_verified: bool = False
    
    # Contract interaction
    is_contract_call: bool = False
    contract_verified: bool = False
    function_name: str | None = None


class PolicyExecutor:
    """
    Executes policies against transactions.
    
    The executor:
    1. Loads all active policies for a user
    2. Sorts them by priority (highest first)
    3. Evaluates each rule in order
    4. Aggregates decisions (most restrictive wins)
    5. Returns final decision with audit trail
    """
    
    def __init__(self, rules: list[PolicyRule] | None = None):
        """
        Initialize executor with optional rules.
        
        In production, rules are loaded from the database.
        """
        self.rules: list[PolicyRule] = rules or []
        self._rule_registry: dict[str, type[PolicyRule]] = {}
    
    def register_rule(self, rule_type: str, rule_class: type[PolicyRule]) -> None:
        """Register a rule type for dynamic loading."""
        self._rule_registry[rule_type] = rule_class
        logger.debug("Registered policy rule", rule_type=rule_type)
    
    def load_rules_from_config(self, policies: list[dict]) -> None:
        """
        Load rules from policy configuration.
        
        Each policy dict should have:
        - rule_type: str
        - config: dict
        - priority: int
        - is_active: bool
        """
        self.rules = []
        
        for policy in policies:
            if not policy.get("is_active", True):
                continue
            
            rule_type = policy.get("rule_type")
            if rule_type not in self._rule_registry:
                logger.warning("Unknown rule type", rule_type=rule_type)
                continue
            
            rule_class = self._rule_registry[rule_type]
            rule = rule_class(
                name=policy.get("name", rule_type),
                config=policy.get("config", {}),
                priority=policy.get("priority", 0)
            )
            self.rules.append(rule)
        
        # Sort by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        
        logger.info("Loaded policy rules", count=len(self.rules))
    
    async def execute(self, tx: TransactionContext) -> ExecutionResult:
        """
        Execute all policies against a transaction.
        
        Returns the most restrictive decision from all rules.
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "Executing policies",
            user_id=tx.user_id,
            chain=tx.chain,
            value_usd=float(tx.value_usd),
            rules_count=len(self.rules)
        )
        
        # Handle duress mode specially
        if tx.duress_mode_active:
            return ExecutionResult(
                decision=DecisionType.ALLOW,  # Allow decoy transactions
                warnings=["DURESS_MODE_ACTIVE"],
                rules_evaluated=["duress_intercept"]
            )
        
        # Collect decisions from all rules
        decisions: list[tuple[PolicyRule, PolicyDecision]] = []
        
        for rule in self.rules:
            try:
                context = PolicyContext(
                    transaction=tx,
                    user_tier=tx.user_tier,
                    current_time=tx.current_time
                )
                
                decision = await rule.evaluate(context)
                decisions.append((rule, decision))
                
                logger.debug(
                    "Rule evaluated",
                    rule=rule.name,
                    allowed=decision.allowed,
                    warnings=decision.warnings
                )
                
            except Exception as e:
                logger.error(
                    "Rule evaluation failed",
                    rule=rule.name,
                    error=str(e)
                )
                # Fail closed - block on error
                return ExecutionResult(
                    decision=DecisionType.BLOCK,
                    blocking_rule=f"{rule.name} (evaluation error)",
                    rules_evaluated=[r.name for r, _ in decisions] + [rule.name]
                )
        
        # Aggregate decisions (most restrictive wins)
        result = self._aggregate_decisions(decisions)
        
        # Calculate execution time
        result.evaluation_time_ms = (
            datetime.utcnow() - start_time
        ).total_seconds() * 1000
        
        logger.info(
            "Policy execution complete",
            decision=result.decision.value,
            blocking_rule=result.blocking_rule,
            eval_time_ms=result.evaluation_time_ms
        )
        
        return result
    
    def _aggregate_decisions(
        self,
        decisions: list[tuple[PolicyRule, PolicyDecision]]
    ) -> ExecutionResult:
        """
        Aggregate multiple policy decisions.
        
        Priority order (most restrictive wins):
        1. BLOCK
        2. DELAY
        3. REQUIRE_2FA
        4. WARN
        5. ALLOW
        """
        final_decision = DecisionType.ALLOW
        blocking_rule = None
        delay_seconds = None
        all_warnings = []
        all_actions = []
        rules_evaluated = []
        
        for rule, decision in decisions:
            rules_evaluated.append(rule.name)
            all_warnings.extend(decision.warnings)
            all_actions.extend(decision.required_actions)
            
            if not decision.allowed:
                # This rule blocks the transaction
                if final_decision != DecisionType.BLOCK:
                    final_decision = DecisionType.BLOCK
                    blocking_rule = rule.name
            
            elif decision.delay_seconds:
                # This rule requires a delay
                if final_decision not in [DecisionType.BLOCK]:
                    final_decision = DecisionType.DELAY
                    if delay_seconds is None or decision.delay_seconds > delay_seconds:
                        delay_seconds = decision.delay_seconds
                        blocking_rule = rule.name
            
            elif decision.require_2fa:
                # This rule requires 2FA
                if final_decision not in [DecisionType.BLOCK, DecisionType.DELAY]:
                    final_decision = DecisionType.REQUIRE_2FA
                    all_actions.append("2fa_required")
            
            elif decision.warnings:
                # This rule has warnings but allows
                if final_decision == DecisionType.ALLOW:
                    final_decision = DecisionType.WARN
        
        return ExecutionResult(
            decision=final_decision,
            blocking_rule=blocking_rule,
            delay_seconds=delay_seconds,
            warnings=list(set(all_warnings)),  # Dedupe
            required_actions=list(set(all_actions)),
            rules_evaluated=rules_evaluated
        )
