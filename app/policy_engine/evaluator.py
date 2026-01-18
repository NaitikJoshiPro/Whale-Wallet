"""
Policy Evaluator

High-level interface for evaluating policies.
Used by the API layer to check transactions.
"""

from decimal import Decimal
from datetime import datetime

import structlog

from app.policy_engine.executor import PolicyExecutor, TransactionContext, ExecutionResult
from app.policy_engine.rules.velocity import VelocityRule
from app.policy_engine.rules.whitelist import WhitelistRule
from app.policy_engine.rules.timelock import TimelockRule

logger = structlog.get_logger(__name__)


class PolicyEvaluator:
    """
    High-level policy evaluation interface.
    
    Provides a simple API for the rest of the application
    to evaluate transactions against user policies.
    """
    
    def __init__(self):
        """Initialize with all registered rule types."""
        self.executor = PolicyExecutor()
        
        # Register all available rule types
        self.executor.register_rule("velocity", VelocityRule)
        self.executor.register_rule("whitelist", WhitelistRule)
        self.executor.register_rule("timelock", TimelockRule)
    
    async def evaluate_transaction(
        self,
        user_id: str,
        user_tier: str,
        policies: list[dict],
        chain: str,
        to_address: str,
        value_usd: Decimal,
        daily_outflow_usd: Decimal = Decimal("0"),
        is_new_address: bool = True,
        is_contract_call: bool = False,
        contract_verified: bool = False,
        duress_mode: bool = False,
        **kwargs
    ) -> ExecutionResult:
        """
        Evaluate a transaction against user policies.
        
        Args:
            user_id: User identifier
            user_tier: Membership tier (orca/humpback/blue)
            policies: List of policy configurations from database
            chain: Blockchain (ethereum, bitcoin, solana, etc.)
            to_address: Destination address
            value_usd: Transaction value in USD
            daily_outflow_usd: Total USD sent in last 24 hours
            is_new_address: Whether destination is new (not seen before)
            is_contract_call: Whether this is a contract interaction
            contract_verified: Whether the contract is verified
            duress_mode: Whether duress mode is active
        
        Returns:
            ExecutionResult with decision and details
        """
        # Load rules from policy config
        self.executor.load_rules_from_config(policies)
        
        # Build transaction context
        context = TransactionContext(
            chain=chain,
            to_address=to_address,
            value_native=Decimal("0"),  # Would be calculated from chain
            value_usd=value_usd,
            user_id=user_id,
            user_tier=user_tier,
            daily_outflow_usd=daily_outflow_usd,
            is_new_address=is_new_address,
            address_in_whitelist=not is_new_address,  # Simplified
            current_time=datetime.utcnow(),
            duress_mode_active=duress_mode,
            is_contract_call=is_contract_call,
            contract_verified=contract_verified
        )
        
        # Execute policies
        result = await self.executor.execute(context)
        
        logger.info(
            "Transaction evaluation complete",
            user_id=user_id,
            decision=result.decision.value,
            rules_evaluated=len(result.rules_evaluated)
        )
        
        return result
    
    async def get_applicable_limits(
        self,
        user_tier: str,
        policies: list[dict]
    ) -> dict:
        """
        Get the effective limits from all policies.
        
        Useful for displaying limits in the UI.
        """
        limits = {
            "daily_limit_usd": float("inf"),
            "per_tx_limit_usd": float("inf"),
            "requires_2fa_above_usd": float("inf"),
            "blocked_hours": [],
            "whitelist_mode": None
        }
        
        for policy in policies:
            if not policy.get("is_active", True):
                continue
            
            config = policy.get("config", {})
            rule_type = policy.get("rule_type")
            
            if rule_type == "velocity":
                if config.get("max_daily_usd"):
                    limits["daily_limit_usd"] = min(
                        limits["daily_limit_usd"],
                        config["max_daily_usd"]
                    )
                if config.get("max_per_tx_usd"):
                    limits["per_tx_limit_usd"] = min(
                        limits["per_tx_limit_usd"],
                        config["max_per_tx_usd"]
                    )
                if config.get("require_2fa_above_usd"):
                    limits["requires_2fa_above_usd"] = min(
                        limits["requires_2fa_above_usd"],
                        config["require_2fa_above_usd"]
                    )
            
            elif rule_type == "timelock":
                start = config.get("block_start_hour")
                end = config.get("block_end_hour")
                if start is not None and end is not None:
                    limits["blocked_hours"].append({
                        "start": start,
                        "end": end,
                        "timezone": config.get("timezone", "UTC")
                    })
            
            elif rule_type == "whitelist":
                limits["whitelist_mode"] = config.get("mode")
        
        # Convert inf to None for JSON serialization
        for key in ["daily_limit_usd", "per_tx_limit_usd", "requires_2fa_above_usd"]:
            if limits[key] == float("inf"):
                limits[key] = None
        
        return limits
