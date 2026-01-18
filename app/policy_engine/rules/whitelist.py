"""
Whitelist Rule

Controls which addresses can receive funds:
- Block mode: Only allow whitelisted addresses
- Warn mode: Warn on non-whitelisted but allow
- Quarantine: Add delay for new addresses
"""

import structlog

from app.policy_engine.rules.base import PolicyRule, PolicyContext, PolicyDecision

logger = structlog.get_logger(__name__)


class WhitelistRule(PolicyRule):
    """
    Whitelist rule implementation.
    
    Configuration options:
    - mode: "block_unknown" or "warn_unknown"
    - require_2fa_for_new: Require 2FA for new addresses
    - quarantine_hours_for_new: Delay (in hours) for new addresses
    """
    
    async def evaluate(self, context: PolicyContext) -> PolicyDecision:
        """Evaluate transaction against whitelist."""
        tx = context.transaction
        
        # Get config
        mode = self.config.get("mode", "warn_unknown")
        require_2fa_new = self.config.get("require_2fa_for_new", False)
        quarantine_hours = self.config.get("quarantine_hours_for_new")
        
        # Check if address is whitelisted
        is_whitelisted = tx.address_in_whitelist
        is_new = tx.is_new_address
        
        if is_whitelisted:
            # Whitelisted address - always allow
            return PolicyDecision.allow()
        
        if is_new:
            logger.info(
                "Whitelist rule: new address detected",
                address=tx.to_address[:10] + "...",
                mode=mode
            )
            
            if mode == "block_unknown":
                return PolicyDecision.block(
                    reason=f"Address {tx.to_address[:10]}... is not in your whitelist. "
                           "Add it to whitelist first."
                )
            
            # Warn mode - allow with conditions
            warnings = [
                f"This is a new address not in your whitelist: {tx.to_address[:10]}..."
            ]
            
            # Check quarantine
            if quarantine_hours:
                return PolicyDecision(
                    allowed=True,
                    delay_seconds=quarantine_hours * 3600,
                    warnings=warnings,
                    reason=f"New address requires {quarantine_hours}h quarantine"
                )
            
            # Check 2FA requirement
            if require_2fa_new:
                return PolicyDecision(
                    allowed=True,
                    require_2fa=True,
                    warnings=warnings,
                    required_actions=["2fa_required"],
                    reason="2FA required for new address"
                )
            
            # Just warn
            return PolicyDecision.allow(warnings=warnings)
        
        # Known address but not whitelisted - allow with warning
        return PolicyDecision.allow(
            warnings=["Consider adding frequently used addresses to your whitelist"]
        )
    
    def validate_config(self) -> list[str]:
        """Validate whitelist rule configuration."""
        errors = []
        
        mode = self.config.get("mode")
        if mode and mode not in ["block_unknown", "warn_unknown"]:
            errors.append("mode must be 'block_unknown' or 'warn_unknown'")
        
        quarantine = self.config.get("quarantine_hours_for_new")
        if quarantine is not None:
            if not isinstance(quarantine, (int, float)) or quarantine < 0:
                errors.append("quarantine_hours_for_new must be a positive number")
        
        return errors
