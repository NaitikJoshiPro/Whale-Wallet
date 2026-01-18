"""
Timelock Rule

Restricts transactions based on time:
- Block during certain hours (e.g., night)
- Block on weekends
- Timezone-aware evaluation
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

import structlog

from app.policy_engine.rules.base import PolicyRule, PolicyContext, PolicyDecision

logger = structlog.get_logger(__name__)


class TimelockRule(PolicyRule):
    """
    Time-based restriction rule implementation.
    
    Configuration options:
    - block_start_hour: Start of blocked period (0-23)
    - block_end_hour: End of blocked period (0-23)
    - timezone: Timezone for evaluation (e.g., "America/New_York")
    - block_weekends: Block transactions on Saturday/Sunday
    """
    
    async def evaluate(self, context: PolicyContext) -> PolicyDecision:
        """Evaluate transaction against time restrictions."""
        tx = context.transaction
        
        # Get config
        start_hour = self.config.get("block_start_hour")
        end_hour = self.config.get("block_end_hour")
        timezone_str = self.config.get("timezone", "UTC")
        block_weekends = self.config.get("block_weekends", False)
        
        # Get current time in user's timezone
        try:
            tz = ZoneInfo(timezone_str)
            current = context.current_time.astimezone(tz)
        except Exception:
            logger.warning("Invalid timezone, using UTC", timezone=timezone_str)
            current = context.current_time
        
        current_hour = current.hour
        current_weekday = current.weekday()  # 0=Monday, 6=Sunday
        
        # Check weekend block
        if block_weekends and current_weekday >= 5:  # Saturday or Sunday
            logger.info(
                "Timelock rule: weekend block",
                day=current.strftime("%A")
            )
            return PolicyDecision.block(
                reason=f"Transactions are blocked on weekends. "
                       f"Try again on Monday."
            )
        
        # Check hour block
        if start_hour is not None and end_hour is not None:
            is_blocked = self._is_in_blocked_period(
                current_hour, start_hour, end_hour
            )
            
            if is_blocked:
                logger.info(
                    "Timelock rule: hour block",
                    current_hour=current_hour,
                    block_start=start_hour,
                    block_end=end_hour
                )
                
                # Calculate when block ends
                if end_hour > current_hour:
                    hours_until = end_hour - current_hour
                else:
                    hours_until = (24 - current_hour) + end_hour
                
                return PolicyDecision.block(
                    reason=f"Transactions are blocked between "
                           f"{start_hour}:00 and {end_hour}:00 ({timezone_str}). "
                           f"Try again in ~{hours_until} hours."
                )
        
        # All time checks passed
        return PolicyDecision.allow()
    
    def _is_in_blocked_period(
        self,
        current: int,
        start: int,
        end: int
    ) -> bool:
        """
        Check if current hour is in blocked period.
        
        Handles overnight periods (e.g., 23:00 - 06:00).
        """
        if start <= end:
            # Normal range (e.g., 09:00 - 17:00)
            return start <= current < end
        else:
            # Overnight range (e.g., 23:00 - 06:00)
            return current >= start or current < end
    
    def validate_config(self) -> list[str]:
        """Validate timelock rule configuration."""
        errors = []
        
        start = self.config.get("block_start_hour")
        end = self.config.get("block_end_hour")
        
        if start is not None:
            if not isinstance(start, int) or not 0 <= start <= 23:
                errors.append("block_start_hour must be 0-23")
        
        if end is not None:
            if not isinstance(end, int) or not 0 <= end <= 23:
                errors.append("block_end_hour must be 0-23")
        
        if (start is None) != (end is None):
            errors.append("block_start_hour and block_end_hour must both be set or both be unset")
        
        tz = self.config.get("timezone")
        if tz:
            try:
                ZoneInfo(tz)
            except Exception:
                errors.append(f"Invalid timezone: {tz}")
        
        return errors
