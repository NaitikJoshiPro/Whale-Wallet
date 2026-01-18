"""
Velocity Limit Rule

Enforces spending limits:
- Maximum per-transaction amount
- Maximum daily outflow
- 2FA requirements above threshold
- Time delays for large amounts
"""

from decimal import Decimal

import structlog

from app.policy_engine.rules.base import PolicyRule, PolicyContext, PolicyDecision

logger = structlog.get_logger(__name__)


class VelocityRule(PolicyRule):
    """
    Velocity limit rule implementation.
    
    Configuration options:
    - max_daily_usd: Maximum daily outflow in USD
    - max_per_tx_usd: Maximum per-transaction amount in USD
    - require_2fa_above_usd: Require 2FA above this amount
    - delay_hours_above_usd: Add delay (in hours) above this amount
    """
    
    async def evaluate(self, context: PolicyContext) -> PolicyDecision:
        """Evaluate transaction against velocity limits."""
        tx = context.transaction
        
        # Get config values with defaults
        max_daily = Decimal(str(self.config.get("max_daily_usd", float("inf"))))
        max_per_tx = Decimal(str(self.config.get("max_per_tx_usd", float("inf"))))
        require_2fa_above = self.config.get("require_2fa_above_usd")
        delay_above = self.config.get("delay_hours_above_usd")
        
        # Check per-transaction limit
        if tx.value_usd > max_per_tx:
            logger.info(
                "Velocity rule: per-tx limit exceeded",
                value_usd=float(tx.value_usd),
                limit_usd=float(max_per_tx)
            )
            return PolicyDecision.block(
                reason=f"Transaction amount ${tx.value_usd:,.2f} exceeds "
                       f"per-transaction limit of ${max_per_tx:,.2f}"
            )
        
        # Check daily limit
        projected_daily = tx.daily_outflow_usd + tx.value_usd
        if projected_daily > max_daily:
            remaining = max_daily - tx.daily_outflow_usd
            logger.info(
                "Velocity rule: daily limit exceeded",
                daily_total=float(projected_daily),
                limit_usd=float(max_daily)
            )
            return PolicyDecision.block(
                reason=f"Transaction would exceed daily limit. "
                       f"Remaining today: ${max(remaining, Decimal('0')):,.2f}"
            )
        
        # Check if delay is required
        if delay_above is not None:
            delay_threshold = Decimal(str(delay_above))
            if tx.value_usd > delay_threshold:
                delay_hours = self.config.get("delay_hours", 24)
                delay_seconds = delay_hours * 3600
                logger.info(
                    "Velocity rule: delay required",
                    value_usd=float(tx.value_usd),
                    threshold_usd=float(delay_threshold),
                    delay_hours=delay_hours
                )
                return PolicyDecision.delay(
                    seconds=delay_seconds,
                    reason=f"Transactions above ${delay_threshold:,.2f} require "
                           f"a {delay_hours}-hour delay"
                )
        
        # Check if 2FA is required
        if require_2fa_above is not None:
            twofa_threshold = Decimal(str(require_2fa_above))
            if tx.value_usd > twofa_threshold:
                logger.info(
                    "Velocity rule: 2FA required",
                    value_usd=float(tx.value_usd),
                    threshold_usd=float(twofa_threshold)
                )
                return PolicyDecision.require_verification("2fa_required")
        
        # All checks passed
        return PolicyDecision.allow()
    
    def validate_config(self) -> list[str]:
        """Validate velocity rule configuration."""
        errors = []
        
        if "max_daily_usd" in self.config:
            try:
                val = Decimal(str(self.config["max_daily_usd"]))
                if val <= 0:
                    errors.append("max_daily_usd must be positive")
            except:
                errors.append("max_daily_usd must be a valid number")
        
        if "max_per_tx_usd" in self.config:
            try:
                val = Decimal(str(self.config["max_per_tx_usd"]))
                if val <= 0:
                    errors.append("max_per_tx_usd must be positive")
            except:
                errors.append("max_per_tx_usd must be a valid number")
        
        return errors
