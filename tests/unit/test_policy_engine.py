"""
Unit Tests for Policy Engine

Tests the core policy execution logic including:
- Velocity limits
- Whitelist rules
- Timelock restrictions
- Decision aggregation
"""

import pytest
from decimal import Decimal
from datetime import datetime

from app.policy_engine.executor import (
    PolicyExecutor,
    TransactionContext,
    DecisionType
)
from app.policy_engine.rules.velocity import VelocityRule
from app.policy_engine.rules.whitelist import WhitelistRule
from app.policy_engine.rules.timelock import TimelockRule
from app.policy_engine.rules.base import PolicyContext


class TestVelocityRule:
    """Tests for velocity limit rule."""
    
    @pytest.fixture
    def velocity_rule(self) -> VelocityRule:
        """Create a velocity rule for testing."""
        return VelocityRule(
            name="Test Velocity",
            config={
                "max_daily_usd": 50000,
                "max_per_tx_usd": 25000,
                "require_2fa_above_usd": 10000
            },
            priority=10
        )
    
    @pytest.fixture
    def transaction_context(self) -> TransactionContext:
        """Create a transaction context for testing."""
        return TransactionContext(
            chain="ethereum",
            to_address="0x742d35Cc6634C0532925a3b844Bc9e7595f8fE89",
            value_native=Decimal("1"),
            value_usd=Decimal("5000"),
            user_id="user123",
            user_tier="humpback",
            daily_outflow_usd=Decimal("10000")
        )
    
    @pytest.mark.asyncio
    async def test_allows_transaction_under_limit(
        self,
        velocity_rule: VelocityRule,
        transaction_context: TransactionContext
    ):
        """Transaction under all limits should be allowed."""
        context = PolicyContext(
            transaction=transaction_context,
            user_tier="humpback",
            current_time=datetime.utcnow()
        )
        
        decision = await velocity_rule.evaluate(context)
        
        assert decision.allowed is True
        assert decision.require_2fa is False
    
    @pytest.mark.asyncio
    async def test_blocks_transaction_over_per_tx_limit(
        self,
        velocity_rule: VelocityRule,
        transaction_context: TransactionContext
    ):
        """Transaction over per-tx limit should be blocked."""
        transaction_context.value_usd = Decimal("30000")  # Over 25k limit
        
        context = PolicyContext(
            transaction=transaction_context,
            user_tier="humpback",
            current_time=datetime.utcnow()
        )
        
        decision = await velocity_rule.evaluate(context)
        
        assert decision.allowed is False
        assert "per-transaction limit" in decision.reason
    
    @pytest.mark.asyncio
    async def test_blocks_transaction_over_daily_limit(
        self,
        velocity_rule: VelocityRule,
        transaction_context: TransactionContext
    ):
        """Transaction that would exceed daily limit should be blocked."""
        transaction_context.value_usd = Decimal("45000")
        transaction_context.daily_outflow_usd = Decimal("10000")
        # Total would be 55k, over 50k daily limit
        
        context = PolicyContext(
            transaction=transaction_context,
            user_tier="humpback",
            current_time=datetime.utcnow()
        )
        
        decision = await velocity_rule.evaluate(context)
        
        assert decision.allowed is False
        assert "daily limit" in decision.reason
    
    @pytest.mark.asyncio
    async def test_requires_2fa_above_threshold(
        self,
        velocity_rule: VelocityRule,
        transaction_context: TransactionContext
    ):
        """Transaction above 2FA threshold should require verification."""
        transaction_context.value_usd = Decimal("15000")  # Over 10k 2FA threshold
        
        context = PolicyContext(
            transaction=transaction_context,
            user_tier="humpback",
            current_time=datetime.utcnow()
        )
        
        decision = await velocity_rule.evaluate(context)
        
        assert decision.allowed is True
        assert decision.require_2fa is True


class TestWhitelistRule:
    """Tests for whitelist rule."""
    
    @pytest.fixture
    def whitelist_rule_block(self) -> WhitelistRule:
        """Create a blocking whitelist rule."""
        return WhitelistRule(
            name="Test Whitelist",
            config={"mode": "block_unknown"},
            priority=5
        )
    
    @pytest.fixture
    def whitelist_rule_warn(self) -> WhitelistRule:
        """Create a warning whitelist rule."""
        return WhitelistRule(
            name="Test Whitelist",
            config={"mode": "warn_unknown", "quarantine_hours_for_new": 24},
            priority=5
        )
    
    @pytest.mark.asyncio
    async def test_allows_whitelisted_address(self, whitelist_rule_block: WhitelistRule):
        """Whitelisted addresses should be allowed."""
        tx = TransactionContext(
            chain="ethereum",
            to_address="0x123",
            value_native=Decimal("1"),
            value_usd=Decimal("5000"),
            address_in_whitelist=True,
            is_new_address=False
        )
        
        context = PolicyContext(
            transaction=tx,
            user_tier="humpback",
            current_time=datetime.utcnow()
        )
        
        decision = await whitelist_rule_block.evaluate(context)
        
        assert decision.allowed is True
    
    @pytest.mark.asyncio
    async def test_blocks_unknown_in_block_mode(self, whitelist_rule_block: WhitelistRule):
        """Unknown addresses should be blocked in block mode."""
        tx = TransactionContext(
            chain="ethereum",
            to_address="0x999",
            value_native=Decimal("1"),
            value_usd=Decimal("5000"),
            address_in_whitelist=False,
            is_new_address=True
        )
        
        context = PolicyContext(
            transaction=tx,
            user_tier="humpback",
            current_time=datetime.utcnow()
        )
        
        decision = await whitelist_rule_block.evaluate(context)
        
        assert decision.allowed is False
    
    @pytest.mark.asyncio
    async def test_delays_unknown_in_warn_mode(self, whitelist_rule_warn: WhitelistRule):
        """Unknown addresses should be delayed in warn mode with quarantine."""
        tx = TransactionContext(
            chain="ethereum",
            to_address="0x999",
            value_native=Decimal("1"),
            value_usd=Decimal("5000"),
            address_in_whitelist=False,
            is_new_address=True
        )
        
        context = PolicyContext(
            transaction=tx,
            user_tier="humpback",
            current_time=datetime.utcnow()
        )
        
        decision = await whitelist_rule_warn.evaluate(context)
        
        assert decision.allowed is True
        assert decision.delay_seconds == 24 * 3600


class TestPolicyExecutor:
    """Tests for the policy executor."""
    
    @pytest.mark.asyncio
    async def test_duress_mode_allows_all(self):
        """Transactions in duress mode should be allowed (decoy)."""
        executor = PolicyExecutor(rules=[
            VelocityRule(
                name="Velocity",
                config={"max_per_tx_usd": 1000},  # Would block
                priority=10
            )
        ])
        
        tx = TransactionContext(
            chain="ethereum",
            to_address="0x123",
            value_native=Decimal("100"),
            value_usd=Decimal("50000"),  # Way over limit
            duress_mode_active=True  # But duress mode is active
        )
        
        result = await executor.execute(tx)
        
        assert result.decision == DecisionType.ALLOW
        assert "DURESS_MODE_ACTIVE" in result.warnings
    
    @pytest.mark.asyncio
    async def test_aggregates_multiple_rules(self):
        """Executor should aggregate decisions from multiple rules."""
        executor = PolicyExecutor(rules=[
            VelocityRule(
                name="Velocity",
                config={"require_2fa_above_usd": 5000},
                priority=10
            ),
            WhitelistRule(
                name="Whitelist",
                config={"mode": "warn_unknown"},
                priority=5
            )
        ])
        
        tx = TransactionContext(
            chain="ethereum",
            to_address="0x123",
            value_native=Decimal("1"),
            value_usd=Decimal("10000"),  # Triggers 2FA
            is_new_address=True  # Triggers warning
        )
        
        result = await executor.execute(tx)
        
        # Should aggregate both rules
        assert len(result.rules_evaluated) == 2
        assert result.decision == DecisionType.REQUIRE_2FA
