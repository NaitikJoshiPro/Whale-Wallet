"""
Transaction API Endpoints

Handles transaction creation, simulation, signing, and history.
This is where the MPC signing and policy engine integration happens.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.auth import get_current_user
from app.config import get_settings, Settings

logger = structlog.get_logger(__name__)
router = APIRouter()


# === Enums & Types ===

class TransactionStatus(str, Enum):
    PENDING = "pending"
    SIMULATING = "simulating"
    AWAITING_APPROVAL = "awaiting_approval"
    SIGNING = "signing"
    BROADCAST = "broadcast"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REJECTED = "rejected"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# === Schemas ===

class TransactionRequest(BaseModel):
    """Transaction creation request."""
    chain: str
    to: str
    value: str = "0"  # In native units (e.g., wei for ETH)
    data: str | None = None  # Contract call data
    gas_limit: int | None = None
    
    # Optional metadata for human-readable display
    recipient_label: str | None = None
    memo: str | None = None


class SimulationResult(BaseModel):
    """Transaction simulation result."""
    success: bool
    
    # Human-readable summary
    summary: str
    
    # Detailed changes
    balance_changes: list[dict]
    token_approvals: list[dict] | None = None
    nft_transfers: list[dict] | None = None
    
    # Risk assessment
    risk_level: RiskLevel
    warnings: list[str]
    
    # Gas estimation
    estimated_gas: int
    estimated_gas_usd: Decimal
    
    # Contract verification
    contract_verified: bool
    contract_name: str | None = None


class TransactionResponse(BaseModel):
    """Transaction response after creation."""
    id: UUID
    status: TransactionStatus
    chain: str
    to: str
    value: str
    value_usd: Decimal
    
    # Simulation results
    simulation: SimulationResult | None = None
    
    # Policy evaluation
    policy_result: dict | None = None
    
    # Timing
    created_at: datetime
    signed_at: datetime | None = None
    broadcast_at: datetime | None = None
    confirmed_at: datetime | None = None
    
    # On-chain data
    tx_hash: str | None = None
    block_number: int | None = None


class TransactionHistoryItem(BaseModel):
    """Transaction history item."""
    id: UUID
    chain: str
    direction: Literal["in", "out"]
    counterparty: str
    counterparty_label: str | None
    value_usd: Decimal
    asset: str
    status: TransactionStatus
    tx_hash: str | None
    timestamp: datetime


class SigningRequest(BaseModel):
    """Request to sign a pending transaction."""
    transaction_id: UUID
    
    # MPC signing requires verification
    biometric_verified: bool = False
    two_factor_code: str | None = None


# === Endpoints ===

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    tx: TransactionRequest,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> TransactionResponse:
    """
    Create a new transaction.
    
    This initiates the transaction flow:
    1. Parse and validate transaction parameters
    2. Run simulation to predict outcomes
    3. Evaluate against user's policies
    4. Return for user approval (if policies allow)
    
    The transaction is NOT signed or broadcast at this stage.
    """
    logger.info(
        "Creating transaction",
        user_id=current_user["user_id"],
        chain=tx.chain,
        to=tx.to
    )
    
    # Simulate the transaction
    simulation = await _simulate_transaction(tx, settings)
    
    # Evaluate policies
    policy_result = await _evaluate_policies(tx, current_user, simulation)
    
    # Determine initial status based on policy result
    if not policy_result.get("allowed"):
        initial_status = TransactionStatus.REJECTED
    elif policy_result.get("requires_delay"):
        initial_status = TransactionStatus.AWAITING_APPROVAL
    else:
        initial_status = TransactionStatus.PENDING
    
    return TransactionResponse(
        id=UUID("44445555-6666-7777-8888-999900001111"),
        status=initial_status,
        chain=tx.chain,
        to=tx.to,
        value=tx.value,
        value_usd=Decimal("15432.10"),
        simulation=simulation,
        policy_result=policy_result,
        created_at=datetime.utcnow()
    )


@router.post("/simulate", response_model=SimulationResult)
async def simulate_transaction(
    tx: TransactionRequest,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> SimulationResult:
    """
    Simulate a transaction without creating it.
    
    This is useful for previewing transaction effects in the UI
    before the user commits to the transaction.
    
    Uses Blowfish or similar simulation service to:
    - Predict balance changes
    - Detect malicious contracts
    - Estimate gas costs
    - Identify token approvals
    """
    return await _simulate_transaction(tx, settings)


@router.post("/{transaction_id}/sign", response_model=TransactionResponse)
async def sign_transaction(
    transaction_id: UUID,
    request: SigningRequest,
    current_user: dict = Depends(get_current_user)
) -> TransactionResponse:
    """
    Sign and broadcast a pending transaction.
    
    This triggers the MPC signing flow:
    1. Mobile app sends Shard A contribution
    2. Server TEE provides Shard B contribution
    3. Combined signature is generated (never exposing full key)
    4. Transaction is broadcast to the network
    
    Requires biometric verification on mobile device.
    May require 2FA if policies demand it.
    """
    if not request.biometric_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Biometric verification required for signing"
        )
    
    logger.info(
        "Signing transaction",
        user_id=current_user["user_id"],
        transaction_id=str(transaction_id)
    )
    
    # In production:
    # 1. Fetch transaction from database
    # 2. Verify it's in PENDING or AWAITING_APPROVAL status
    # 3. Re-check policies (they may have changed)
    # 4. Initiate MPC signing protocol with TEE
    # 5. Broadcast signed transaction
    # 6. Update status and store tx_hash
    
    return TransactionResponse(
        id=transaction_id,
        status=TransactionStatus.BROADCAST,
        chain="ethereum",
        to="0x742d35Cc6634C0532925a3b844Bc9e7595f8fE89",
        value="1000000000000000000",  # 1 ETH in wei
        value_usd=Decimal("2345.67"),
        simulation=None,
        policy_result={"allowed": True},
        created_at=datetime.utcnow(),
        signed_at=datetime.utcnow(),
        broadcast_at=datetime.utcnow(),
        tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    )


@router.post("/{transaction_id}/cancel")
async def cancel_transaction(
    transaction_id: UUID,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Cancel a pending transaction.
    
    Only possible for transactions that haven't been broadcast yet.
    Once a transaction is on-chain, it cannot be cancelled (though
    it may be replaceable with a higher gas price).
    """
    logger.info(
        "Cancelling transaction",
        user_id=current_user["user_id"],
        transaction_id=str(transaction_id)
    )
    
    return {
        "status": "cancelled",
        "transaction_id": str(transaction_id),
        "message": "Transaction cancelled successfully"
    }


@router.get("/history", response_model=list[TransactionHistoryItem])
async def get_transaction_history(
    current_user: dict = Depends(get_current_user),
    chain: str | None = None,
    limit: int = 50,
    offset: int = 0
) -> list[TransactionHistoryItem]:
    """
    Get transaction history.
    
    Returns both incoming and outgoing transactions across
    all supported chains (or filtered by chain).
    """
    # Mock data - in production, query from database and on-chain
    return [
        TransactionHistoryItem(
            id=UUID("11112222-3333-4444-5555-666677778888"),
            chain="ethereum",
            direction="out",
            counterparty="0x742d35Cc6634C0532925a3b844Bc9e7595f8fE89",
            counterparty_label="alice.eth",
            value_usd=Decimal("5000.00"),
            asset="ETH",
            status=TransactionStatus.CONFIRMED,
            tx_hash="0xabcd1234...",
            timestamp=datetime(2024, 6, 1, 14, 30)
        ),
        TransactionHistoryItem(
            id=UUID("22223333-4444-5555-6666-777788889999"),
            chain="ethereum",
            direction="in",
            counterparty="0x123456789abcdef123456789abcdef1234567890",
            counterparty_label="Coinbase",
            value_usd=Decimal("25000.00"),
            asset="USDC",
            status=TransactionStatus.CONFIRMED,
            tx_hash="0xef561234...",
            timestamp=datetime(2024, 5, 28, 10, 15)
        )
    ]


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: dict = Depends(get_current_user)
) -> TransactionResponse:
    """Get details of a specific transaction."""
    # In production, fetch from database
    
    return TransactionResponse(
        id=transaction_id,
        status=TransactionStatus.CONFIRMED,
        chain="ethereum",
        to="0x742d35Cc6634C0532925a3b844Bc9e7595f8fE89",
        value="1000000000000000000",
        value_usd=Decimal("2345.67"),
        created_at=datetime(2024, 6, 1, 14, 25),
        signed_at=datetime(2024, 6, 1, 14, 28),
        broadcast_at=datetime(2024, 6, 1, 14, 28),
        confirmed_at=datetime(2024, 6, 1, 14, 30),
        tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        block_number=18500000
    )


# === Helper Functions ===

async def _simulate_transaction(
    tx: TransactionRequest,
    settings: Settings
) -> SimulationResult:
    """
    Simulate transaction using Blowfish or similar service.
    
    In production, this calls the Blowfish API to get detailed
    simulation results including:
    - Balance changes for all tokens
    - Token approvals being granted
    - NFT transfers
    - Risk assessment
    """
    # Mock simulation result
    # In production, call Blowfish API
    
    is_contract = tx.data is not None and len(tx.data) > 2
    
    return SimulationResult(
        success=True,
        summary=f"Send {tx.value} to {tx.to[:10]}...",
        balance_changes=[
            {
                "asset": "ETH",
                "change": f"-{tx.value}",
                "usd_change": "-2345.67"
            }
        ],
        token_approvals=None,
        nft_transfers=None,
        risk_level=RiskLevel.LOW if not is_contract else RiskLevel.MEDIUM,
        warnings=[
            "New address - not in your whitelist"
        ] if True else [],  # Check whitelist in production
        estimated_gas=21000 if not is_contract else 150000,
        estimated_gas_usd=Decimal("3.50"),
        contract_verified=True,
        contract_name="Uniswap V3 Router" if is_contract else None
    )


async def _evaluate_policies(
    tx: TransactionRequest,
    current_user: dict,
    simulation: SimulationResult
) -> dict:
    """
    Evaluate transaction against user's policies.
    
    In production, this queries all active policies and runs
    them through the policy engine.
    """
    # Mock policy evaluation
    # In production, delegate to policy engine
    
    return {
        "allowed": True,
        "checked_policies": ["velocity", "whitelist", "timelock"],
        "warnings": simulation.warnings,
        "requires_delay": False,
        "requires_2fa": False
    }
