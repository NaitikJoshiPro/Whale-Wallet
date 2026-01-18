"""
Wallet API Endpoints

Core wallet operations including balance queries, address management,
and MPC key operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.auth import get_current_user
from app.config import get_settings, Settings
from app.chains import (
    CHAIN_REGISTRY,
    CHAIN_STATS,
    get_all_chains,
    get_chain,
    get_evm_chains,
    is_chain_supported,
    ChainConfig,
    SigningCurve,
    ChainType
)

logger = structlog.get_logger(__name__)
router = APIRouter()


# === Schemas ===

class ChainBalance(BaseModel):
    """Balance on a specific chain."""
    chain: str
    native_balance: Decimal
    native_symbol: str
    usd_value: Decimal
    tokens: list[dict]


class WalletOverview(BaseModel):
    """Complete wallet overview across all chains."""
    total_usd_value: Decimal
    chains: list[ChainBalance]
    last_updated: datetime
    pending_transactions: int


class AddressInfo(BaseModel):
    """Wallet address information."""
    chain: str
    address: str
    derivation_path: str
    is_primary: bool


class MPCStatus(BaseModel):
    """MPC key status."""
    shard_a_status: str  # 'active', 'locked', 'compromised'
    shard_b_status: str
    shard_c_status: str
    last_key_rotation: datetime | None
    requires_rotation: bool


class InheritancePing(BaseModel):
    """Inheritance Dead Man's Switch ping."""
    last_ping: datetime
    next_required: datetime
    days_until_trigger: int
    guardians_configured: int


class ChainInfo(BaseModel):
    """Blockchain chain information."""
    key: str
    chain_id: str
    name: str
    symbol: str
    chain_type: str
    signing_curve: str
    decimals: int
    explorer_url: str
    mpc_compatible: bool


class ChainStatsResponse(BaseModel):
    """Chain registry statistics."""
    total_chains: int
    evm_chains: int
    ecdsa_chains: int
    eddsa_chains: int
    supported_symbols: list[str]


# === Endpoints ===


@router.get("/overview", response_model=WalletOverview)
async def get_wallet_overview(
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> WalletOverview:
    """
    Get complete wallet overview.
    
    Aggregates balances across all supported chains and tokens,
    including DeFi positions and staked assets.
    """
    logger.info("Fetching wallet overview", user_id=current_user["user_id"])
    
    # In production, this would:
    # 1. Query all chain RPC endpoints for native balances
    # 2. Query token balances via multicall
    # 3. Fetch DeFi positions from protocols
    # 4. Aggregate USD values from price oracles
    
    return WalletOverview(
        total_usd_value=Decimal("1234567.89"),
        chains=[
            ChainBalance(
                chain="ethereum",
                native_balance=Decimal("45.123"),
                native_symbol="ETH",
                usd_value=Decimal("987654.32"),
                tokens=[
                    {"symbol": "USDC", "balance": "100000", "usd_value": "100000"},
                    {"symbol": "WBTC", "balance": "1.5", "usd_value": "150000"}
                ]
            ),
            ChainBalance(
                chain="solana",
                native_balance=Decimal("500"),
                native_symbol="SOL",
                usd_value=Decimal("50000"),
                tokens=[]
            )
        ],
        last_updated=datetime.utcnow(),
        pending_transactions=0
    )


@router.get("/addresses", response_model=list[AddressInfo])
async def get_wallet_addresses(
    current_user: dict = Depends(get_current_user)
) -> list[AddressInfo]:
    """
    Get all wallet addresses across supported chains.
    
    Each chain may have multiple addresses derived from the MPC master key.
    """
    # In production, derive addresses from MPC public key
    
    return [
        AddressInfo(
            chain="ethereum",
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f8fE89",
            derivation_path="m/44'/60'/0'/0/0",
            is_primary=True
        ),
        AddressInfo(
            chain="bitcoin",
            address="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            derivation_path="m/84'/0'/0'/0/0",
            is_primary=True
        ),
        AddressInfo(
            chain="solana",
            address="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            derivation_path="m/44'/501'/0'/0'",
            is_primary=True
        )
    ]


@router.get("/mpc/status", response_model=MPCStatus)
async def get_mpc_status(
    current_user: dict = Depends(get_current_user)
) -> MPCStatus:
    """
    Get MPC key shard status.
    
    Shows the health of all three key shards:
    - Shard A (Mobile): In user's Secure Enclave
    - Shard B (Server): In cloud TEE
    - Shard C (Recovery): With guardians or in backup
    """
    # In production, verify shard availability with each storage location
    
    return MPCStatus(
        shard_a_status="active",
        shard_b_status="active",
        shard_c_status="active",
        last_key_rotation=datetime(2024, 6, 15),
        requires_rotation=False
    )


@router.post("/mpc/rotate")
async def initiate_key_rotation(
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> dict:
    """
    Initiate MPC key rotation.
    
    Key rotation (resharing) creates new shards without changing
    the underlying public key or blockchain addresses. This is
    recommended periodically for security.
    
    Process:
    1. Generate new random polynomial
    2. Each shard holder contributes to new shares
    3. Old shares are invalidated
    4. No on-chain transaction required
    """
    logger.info("Key rotation initiated", user_id=current_user["user_id"])
    
    # In production, trigger MPC coordinator to start reshare protocol
    
    return {
        "status": "rotation_initiated",
        "message": "Key rotation started. Complete biometric verification on mobile.",
        "expiry_minutes": 15
    }


@router.get("/inheritance/status", response_model=InheritancePing)
async def get_inheritance_status(
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> InheritancePing:
    """
    Get Dead Man's Switch status for inheritance.
    
    The inheritance protocol triggers if the user fails to
    authenticate for a configured period (e.g., 180 days).
    """
    if not settings.enable_inheritance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inheritance feature not enabled"
        )
    
    # In production, fetch from inheritance_config table
    
    last_ping = datetime.utcnow()
    threshold_days = 180
    
    return InheritancePing(
        last_ping=last_ping,
        next_required=datetime(2024, 12, 31),
        days_until_trigger=threshold_days,
        guardians_configured=3
    )


@router.post("/inheritance/ping")
async def ping_inheritance(
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> dict:
    """
    Ping the Dead Man's Switch.
    
    Resets the inheritance timer. This is automatically called
    on each biometric authentication but can also be manually
    triggered.
    """
    if not settings.enable_inheritance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inheritance feature not enabled"
        )
    
    logger.info("Inheritance ping", user_id=current_user["user_id"])
    
    # In production, update last_ping_at in inheritance_config
    
    return {
        "status": "pinged",
        "next_required": datetime(2025, 6, 15).isoformat(),
        "message": "Dead Man's Switch reset successfully"
    }


@router.get("/stealth/decoy")
async def get_decoy_wallet(
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> WalletOverview:
    """
    Get decoy wallet data for duress mode.
    
    Returns a plausible-looking wallet with modest balances
    and realistic transaction history. This is shown when
    duress mode is active.
    """
    if not settings.enable_duress_mode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    # Return convincing but modest decoy data
    return WalletOverview(
        total_usd_value=Decimal("5432.10"),
        chains=[
            ChainBalance(
                chain="ethereum",
                native_balance=Decimal("1.234"),
                native_symbol="ETH",
                usd_value=Decimal("4321.00"),
                tokens=[
                    {"symbol": "USDC", "balance": "1000", "usd_value": "1000"}
                ]
            )
        ],
        last_updated=datetime.utcnow(),
        pending_transactions=0
    )


@router.get("/chains", response_model=list[ChainInfo])
async def get_supported_chains() -> list[ChainInfo]:
    """
    Get all supported blockchain chains.
    
    Returns configuration for all 18 supported chains including:
    - Chain identifiers and names
    - Native token symbols
    - Signing curve requirements
    - MPC compatibility status
    """
    chains_list = []
    for key, config in CHAIN_REGISTRY.items():
        chains_list.append(ChainInfo(
            key=key,
            chain_id=config.chain_id,
            name=config.name,
            symbol=config.symbol,
            chain_type=config.chain_type.value,
            signing_curve=config.signing_curve.value,
            decimals=config.decimals,
            explorer_url=config.explorer_url,
            mpc_compatible=config.mpc_compatible
        ))
    return chains_list


@router.get("/chains/stats", response_model=ChainStatsResponse)
async def get_chain_stats() -> ChainStatsResponse:
    """
    Get chain registry statistics.
    
    Returns aggregate statistics about supported chains.
    """
    return ChainStatsResponse(**CHAIN_STATS)


@router.get("/chains/{chain_key}", response_model=ChainInfo)
async def get_chain_info(chain_key: str) -> ChainInfo:
    """
    Get information about a specific chain.
    
    Args:
        chain_key: Chain identifier (e.g., 'ethereum', 'solana')
        
    Returns:
        Chain configuration details
        
    Raises:
        404 if chain is not supported
    """
    config = get_chain(chain_key)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chain '{chain_key}' is not supported. Use /wallet/chains for supported chains."
        )
    
    return ChainInfo(
        key=chain_key.lower(),
        chain_id=config.chain_id,
        name=config.name,
        symbol=config.symbol,
        chain_type=config.chain_type.value,
        signing_curve=config.signing_curve.value,
        decimals=config.decimals,
        explorer_url=config.explorer_url,
        mpc_compatible=config.mpc_compatible
    )
