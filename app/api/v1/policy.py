"""
Policy Engine API Endpoints

CRUD operations for the Global Rule Engine that governs
all transaction signing decisions.

Policy Types:
- velocity: Spending limits (daily, per-tx)
- whitelist: Allowed destination addresses
- timelock: Time-based restrictions
- chain: Chain-specific rules
- duress: Panic mode behavior
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.auth import get_current_user
from app.config import get_settings, Settings

logger = structlog.get_logger(__name__)
router = APIRouter()


# === Schemas ===

PolicyType = Literal["velocity", "whitelist", "timelock", "chain", "duress", "gas"]


class VelocityConfig(BaseModel):
    """Velocity limit configuration."""
    max_daily_usd: float = Field(..., gt=0)
    max_per_tx_usd: float = Field(..., gt=0)
    require_2fa_above_usd: float | None = None
    delay_hours_above_usd: int | None = None


class WhitelistConfig(BaseModel):
    """Whitelist configuration."""
    mode: Literal["block_unknown", "warn_unknown"] = "warn_unknown"
    require_2fa_for_new: bool = True
    quarantine_hours_for_new: int = 24


class TimelockConfig(BaseModel):
    """Time-based restriction configuration."""
    block_start_hour: int = Field(..., ge=0, le=23)
    block_end_hour: int = Field(..., ge=0, le=23)
    timezone: str = "UTC"
    block_weekends: bool = False


class ChainConfig(BaseModel):
    """Chain-specific rule configuration."""
    chain: str
    block_unverified_contracts: bool = True
    max_gas_gwei: int | None = None
    allowed_protocols: list[str] | None = None


class DuressConfig(BaseModel):
    """Duress mode configuration."""
    duress_pin_hash: str  # Never store plaintext
    notify_contacts: list[str] = []
    decoy_wallet_id: str | None = None
    silent_mode: bool = True


class PolicyBase(BaseModel):
    """Base policy model."""
    rule_type: PolicyType
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    is_active: bool = True
    priority: int = Field(default=0, ge=-100, le=100)


class PolicyCreate(PolicyBase):
    """Policy creation request."""
    config: dict  # Type depends on rule_type


class PolicyUpdate(BaseModel):
    """Policy update request."""
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    priority: int | None = None
    config: dict | None = None


class PolicyResponse(PolicyBase):
    """Policy response model."""
    id: UUID
    user_id: UUID
    config: dict
    created_at: datetime
    updated_at: datetime | None


class PolicyEvaluationResult(BaseModel):
    """Result of evaluating a transaction against policies."""
    allowed: bool
    blocking_policy: str | None = None
    warnings: list[str] = []
    required_actions: list[str] = []
    delay_seconds: int | None = None


# === Endpoints ===

@router.get("", response_model=list[PolicyResponse])
async def list_policies(
    current_user: dict = Depends(get_current_user),
    active_only: bool = True
) -> list[PolicyResponse]:
    """
    List all policies for the current user.
    
    Policies are returned in priority order (highest first).
    Higher priority policies are evaluated first and can
    override lower priority ones.
    """
    logger.info(
        "Listing policies",
        user_id=current_user["user_id"],
        active_only=active_only
    )
    
    # Mock data - in production, fetch from database
    return [
        PolicyResponse(
            id=UUID("12345678-1234-1234-1234-123456789abc"),
            user_id=UUID("87654321-4321-4321-4321-cba987654321"),
            rule_type="velocity",
            name="Daily Spending Limit",
            description="Limit daily outflow to $50,000",
            is_active=True,
            priority=10,
            config={
                "max_daily_usd": 50000,
                "max_per_tx_usd": 25000,
                "require_2fa_above_usd": 10000,
                "delay_hours_above_usd": None
            },
            created_at=datetime(2024, 1, 15),
            updated_at=None
        ),
        PolicyResponse(
            id=UUID("22345678-1234-1234-1234-123456789abc"),
            user_id=UUID("87654321-4321-4321-4321-cba987654321"),
            rule_type="timelock",
            name="Night Block",
            description="Block large transfers between 11 PM and 6 AM",
            is_active=True,
            priority=20,
            config={
                "block_start_hour": 23,
                "block_end_hour": 6,
                "timezone": "America/New_York",
                "block_weekends": False
            },
            created_at=datetime(2024, 2, 1),
            updated_at=datetime(2024, 3, 15)
        )
    ]


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy: PolicyCreate,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> PolicyResponse:
    """
    Create a new policy.
    
    Policies are enforced by the server-side TEE during MPC signing.
    Even if a user's device is compromised, the server will reject
    transactions that violate the configured policies.
    """
    # Check tier permissions
    tier_limits = settings.tier_limits.get(current_user["tier"], {})
    if not tier_limits.get("advanced_policies") and policy.rule_type in ["timelock", "chain", "duress"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Advanced policy type '{policy.rule_type}' requires Humpback tier or higher"
        )
    
    logger.info(
        "Creating policy",
        user_id=current_user["user_id"],
        rule_type=policy.rule_type,
        name=policy.name
    )
    
    # Validate config based on rule_type
    # In production, use Pydantic models for each config type
    
    # Mock response - in production, save to database
    return PolicyResponse(
        id=UUID("33345678-1234-1234-1234-123456789abc"),
        user_id=UUID("87654321-4321-4321-4321-cba987654321"),
        rule_type=policy.rule_type,
        name=policy.name,
        description=policy.description,
        is_active=policy.is_active,
        priority=policy.priority,
        config=policy.config,
        created_at=datetime.utcnow(),
        updated_at=None
    )


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: UUID,
    current_user: dict = Depends(get_current_user)
) -> PolicyResponse:
    """Get a specific policy by ID."""
    # In production, fetch from database and verify ownership
    
    return PolicyResponse(
        id=policy_id,
        user_id=UUID("87654321-4321-4321-4321-cba987654321"),
        rule_type="velocity",
        name="Daily Spending Limit",
        description="Limit daily outflow to $50,000",
        is_active=True,
        priority=10,
        config={"max_daily_usd": 50000, "max_per_tx_usd": 25000},
        created_at=datetime(2024, 1, 15),
        updated_at=None
    )


@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: UUID,
    updates: PolicyUpdate,
    current_user: dict = Depends(get_current_user)
) -> PolicyResponse:
    """
    Update an existing policy.
    
    Only provided fields are updated. Omitted fields remain unchanged.
    """
    logger.info(
        "Updating policy",
        user_id=current_user["user_id"],
        policy_id=str(policy_id)
    )
    
    # In production, fetch, update, and save to database
    
    return PolicyResponse(
        id=policy_id,
        user_id=UUID("87654321-4321-4321-4321-cba987654321"),
        rule_type="velocity",
        name=updates.name or "Daily Spending Limit",
        description=updates.description,
        is_active=updates.is_active if updates.is_active is not None else True,
        priority=updates.priority or 10,
        config=updates.config or {"max_daily_usd": 50000},
        created_at=datetime(2024, 1, 15),
        updated_at=datetime.utcnow()
    )


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a policy.
    
    Deletion is permanent. Consider deactivating (is_active=False)
    instead if you may want to restore the policy later.
    """
    logger.info(
        "Deleting policy",
        user_id=current_user["user_id"],
        policy_id=str(policy_id)
    )
    
    # In production, delete from database
    return None


@router.post("/evaluate", response_model=PolicyEvaluationResult)
async def evaluate_transaction(
    transaction: dict,
    current_user: dict = Depends(get_current_user)
) -> PolicyEvaluationResult:
    """
    Dry-run policy evaluation for a transaction.
    
    This allows the mobile app to check if a transaction would
    be allowed BEFORE attempting to sign it. Useful for showing
    warnings in the UI.
    
    Input transaction format:
    {
        "chain": "ethereum",
        "to": "0x...",
        "value_usd": 15000,
        "contract_interaction": true,
        "function_name": "transfer"
    }
    """
    logger.info(
        "Evaluating transaction against policies",
        user_id=current_user["user_id"],
        chain=transaction.get("chain"),
        value_usd=transaction.get("value_usd")
    )
    
    # In production, run full policy engine evaluation
    # This is a mock response
    
    value_usd = transaction.get("value_usd", 0)
    
    if value_usd > 50000:
        return PolicyEvaluationResult(
            allowed=False,
            blocking_policy="Daily Spending Limit",
            warnings=["Transaction exceeds daily limit"],
            required_actions=["Increase velocity limit or wait 24 hours"]
        )
    
    if value_usd > 10000:
        return PolicyEvaluationResult(
            allowed=True,
            warnings=["Transaction requires 2FA confirmation"],
            required_actions=["2fa_required"]
        )
    
    return PolicyEvaluationResult(
        allowed=True,
        warnings=[],
        required_actions=[]
    )


@router.get("/templates", response_model=list[dict])
async def get_policy_templates(
    current_user: dict = Depends(get_current_user)
) -> list[dict]:
    """
    Get recommended policy templates.
    
    These are pre-configured policies based on best practices
    for different security profiles. Users can apply these
    as a starting point and customize as needed.
    """
    return [
        {
            "name": "Conservative HNWI",
            "description": "Maximum security for large portfolios",
            "policies": [
                {
                    "rule_type": "velocity",
                    "config": {"max_daily_usd": 50000, "require_2fa_above_usd": 5000}
                },
                {
                    "rule_type": "timelock",
                    "config": {"block_start_hour": 22, "block_end_hour": 7}
                },
                {
                    "rule_type": "whitelist",
                    "config": {"mode": "block_unknown", "quarantine_hours_for_new": 48}
                }
            ]
        },
        {
            "name": "Active Trader",
            "description": "Balanced security for frequent transactions",
            "policies": [
                {
                    "rule_type": "velocity",
                    "config": {"max_daily_usd": 200000, "require_2fa_above_usd": 25000}
                },
                {
                    "rule_type": "chain",
                    "config": {"block_unverified_contracts": True, "max_gas_gwei": 200}
                }
            ]
        },
        {
            "name": "Cold Storage",
            "description": "Ultra-paranoid long-term holding",
            "policies": [
                {
                    "rule_type": "velocity",
                    "config": {"max_daily_usd": 10000, "delay_hours_above_usd": 24}
                },
                {
                    "rule_type": "timelock",
                    "config": {"block_weekends": True}
                },
                {
                    "rule_type": "whitelist",
                    "config": {"mode": "block_unknown"}
                }
            ]
        }
    ]
