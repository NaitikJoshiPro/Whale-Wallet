"""
Whale Wallet Chain Registry

Comprehensive blockchain registry supporting the top 18 chains by market cap
and ecosystem activity. Each chain includes configuration for MPC signing,
address derivation, and RPC connectivity.

Supported Signing Curves:
- ECDSA secp256k1: Bitcoin, Ethereum, and EVM-compatible chains
- EdDSA Ed25519: Solana, Cardano, TON, Near, Sui, Aptos
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SigningCurve(str, Enum):
    """Cryptographic curves supported by the MPC layer."""
    ECDSA_SECP256K1 = "secp256k1"
    EDDSA_ED25519 = "ed25519"


class ChainType(str, Enum):
    """Blockchain architecture type."""
    UTXO = "utxo"          # Bitcoin-style
    EVM = "evm"            # Ethereum Virtual Machine
    SVM = "svm"            # Solana Virtual Machine
    MOVE = "move"          # Move-based (Sui, Aptos)
    WASM = "wasm"          # WebAssembly-based
    CUSTOM = "custom"      # Chain-specific


class AddressFormat(str, Enum):
    """Address encoding format."""
    BASE58 = "base58"           # Bitcoin, Solana
    HEX_CHECKSUM = "hex"        # Ethereum/EVM
    BECH32 = "bech32"           # Bitcoin SegWit
    BECH32M = "bech32m"         # Bitcoin Taproot
    SS58 = "ss58"               # Polkadot
    CUSTOM = "custom"           # Chain-specific


@dataclass(frozen=True)
class ChainConfig:
    """
    Immutable blockchain configuration.
    
    Attributes:
        chain_id: Unique chain identifier (numeric for EVM, string for others)
        name: Human-readable chain name
        symbol: Native token symbol
        chain_type: Architecture type (EVM, UTXO, etc.)
        signing_curve: Cryptographic curve for key derivation
        address_format: Address encoding standard
        decimals: Native token decimals
        rpc_env_var: Environment variable name for RPC endpoint
        default_rpc: Fallback public RPC (rate limited)
        explorer_url: Block explorer base URL
        is_testnet: Whether this is a testnet configuration
        eip155: Whether chain supports EIP-155 replay protection
        supports_eip1559: Whether chain supports EIP-1559 gas model
        mpc_compatible: Whether chain is compatible with MPC signing
    """
    chain_id: str
    name: str
    symbol: str
    chain_type: ChainType
    signing_curve: SigningCurve
    address_format: AddressFormat
    decimals: int
    rpc_env_var: str
    default_rpc: str
    explorer_url: str
    is_testnet: bool = False
    eip155: bool = False
    supports_eip1559: bool = False
    mpc_compatible: bool = True
    coin_type: int = 60  # BIP-44 coin type


# =============================================================================
# CHAIN REGISTRY - Top 18 Blockchains by Market Cap & Ecosystem Activity
# =============================================================================

CHAIN_REGISTRY: dict[str, ChainConfig] = {
    # --- Bitcoin ---
    "bitcoin": ChainConfig(
        chain_id="bitcoin",
        name="Bitcoin",
        symbol="BTC",
        chain_type=ChainType.UTXO,
        signing_curve=SigningCurve.ECDSA_SECP256K1,
        address_format=AddressFormat.BECH32,
        decimals=8,
        rpc_env_var="WHALE_BITCOIN_RPC",
        default_rpc="https://btc.llamarpc.com",
        explorer_url="https://blockstream.info",
        coin_type=0,
    ),
    
    # --- Ethereum & Layer 2s ---
    "ethereum": ChainConfig(
        chain_id="1",
        name="Ethereum",
        symbol="ETH",
        chain_type=ChainType.EVM,
        signing_curve=SigningCurve.ECDSA_SECP256K1,
        address_format=AddressFormat.HEX_CHECKSUM,
        decimals=18,
        rpc_env_var="WHALE_ETHEREUM_RPC",
        default_rpc="https://eth.llamarpc.com",
        explorer_url="https://etherscan.io",
        eip155=True,
        supports_eip1559=True,
        coin_type=60,
    ),
    "arbitrum": ChainConfig(
        chain_id="42161",
        name="Arbitrum One",
        symbol="ETH",
        chain_type=ChainType.EVM,
        signing_curve=SigningCurve.ECDSA_SECP256K1,
        address_format=AddressFormat.HEX_CHECKSUM,
        decimals=18,
        rpc_env_var="WHALE_ARBITRUM_RPC",
        default_rpc="https://arb1.arbitrum.io/rpc",
        explorer_url="https://arbiscan.io",
        eip155=True,
        supports_eip1559=True,
        coin_type=60,
    ),
    "optimism": ChainConfig(
        chain_id="10",
        name="Optimism",
        symbol="ETH",
        chain_type=ChainType.EVM,
        signing_curve=SigningCurve.ECDSA_SECP256K1,
        address_format=AddressFormat.HEX_CHECKSUM,
        decimals=18,
        rpc_env_var="WHALE_OPTIMISM_RPC",
        default_rpc="https://mainnet.optimism.io",
        explorer_url="https://optimistic.etherscan.io",
        eip155=True,
        supports_eip1559=True,
        coin_type=60,
    ),
    "base": ChainConfig(
        chain_id="8453",
        name="Base",
        symbol="ETH",
        chain_type=ChainType.EVM,
        signing_curve=SigningCurve.ECDSA_SECP256K1,
        address_format=AddressFormat.HEX_CHECKSUM,
        decimals=18,
        rpc_env_var="WHALE_BASE_RPC",
        default_rpc="https://mainnet.base.org",
        explorer_url="https://basescan.org",
        eip155=True,
        supports_eip1559=True,
        coin_type=60,
    ),
    "polygon": ChainConfig(
        chain_id="137",
        name="Polygon",
        symbol="MATIC",
        chain_type=ChainType.EVM,
        signing_curve=SigningCurve.ECDSA_SECP256K1,
        address_format=AddressFormat.HEX_CHECKSUM,
        decimals=18,
        rpc_env_var="WHALE_POLYGON_RPC",
        default_rpc="https://polygon-rpc.com",
        explorer_url="https://polygonscan.com",
        eip155=True,
        supports_eip1559=True,
        coin_type=60,
    ),
    
    # --- Other EVM Chains ---
    "bsc": ChainConfig(
        chain_id="56",
        name="BNB Smart Chain",
        symbol="BNB",
        chain_type=ChainType.EVM,
        signing_curve=SigningCurve.ECDSA_SECP256K1,
        address_format=AddressFormat.HEX_CHECKSUM,
        decimals=18,
        rpc_env_var="WHALE_BSC_RPC",
        default_rpc="https://bsc-dataseed.binance.org",
        explorer_url="https://bscscan.com",
        eip155=True,
        supports_eip1559=False,
        coin_type=60,
    ),
    "avalanche": ChainConfig(
        chain_id="43114",
        name="Avalanche C-Chain",
        symbol="AVAX",
        chain_type=ChainType.EVM,
        signing_curve=SigningCurve.ECDSA_SECP256K1,
        address_format=AddressFormat.HEX_CHECKSUM,
        decimals=18,
        rpc_env_var="WHALE_AVALANCHE_RPC",
        default_rpc="https://api.avax.network/ext/bc/C/rpc",
        explorer_url="https://snowtrace.io",
        eip155=True,
        supports_eip1559=True,
        coin_type=60,
    ),
    "fantom": ChainConfig(
        chain_id="250",
        name="Fantom Opera",
        symbol="FTM",
        chain_type=ChainType.EVM,
        signing_curve=SigningCurve.ECDSA_SECP256K1,
        address_format=AddressFormat.HEX_CHECKSUM,
        decimals=18,
        rpc_env_var="WHALE_FANTOM_RPC",
        default_rpc="https://rpc.ftm.tools",
        explorer_url="https://ftmscan.com",
        eip155=True,
        supports_eip1559=False,
        coin_type=60,
    ),
    
    # --- Solana ---
    "solana": ChainConfig(
        chain_id="solana",
        name="Solana",
        symbol="SOL",
        chain_type=ChainType.SVM,
        signing_curve=SigningCurve.EDDSA_ED25519,
        address_format=AddressFormat.BASE58,
        decimals=9,
        rpc_env_var="WHALE_SOLANA_RPC",
        default_rpc="https://api.mainnet-beta.solana.com",
        explorer_url="https://solscan.io",
        coin_type=501,
    ),
    
    # --- Move-based Chains ---
    "sui": ChainConfig(
        chain_id="sui",
        name="Sui",
        symbol="SUI",
        chain_type=ChainType.MOVE,
        signing_curve=SigningCurve.EDDSA_ED25519,
        address_format=AddressFormat.HEX_CHECKSUM,
        decimals=9,
        rpc_env_var="WHALE_SUI_RPC",
        default_rpc="https://fullnode.mainnet.sui.io",
        explorer_url="https://suiscan.xyz",
        coin_type=784,
    ),
    "aptos": ChainConfig(
        chain_id="aptos",
        name="Aptos",
        symbol="APT",
        chain_type=ChainType.MOVE,
        signing_curve=SigningCurve.EDDSA_ED25519,
        address_format=AddressFormat.HEX_CHECKSUM,
        decimals=8,
        rpc_env_var="WHALE_APTOS_RPC",
        default_rpc="https://fullnode.mainnet.aptoslabs.com/v1",
        explorer_url="https://aptoscan.com",
        coin_type=637,
    ),
    
    # --- Cosmos Ecosystem ---
    "cosmos": ChainConfig(
        chain_id="cosmoshub-4",
        name="Cosmos Hub",
        symbol="ATOM",
        chain_type=ChainType.CUSTOM,
        signing_curve=SigningCurve.ECDSA_SECP256K1,
        address_format=AddressFormat.BECH32,
        decimals=6,
        rpc_env_var="WHALE_COSMOS_RPC",
        default_rpc="https://cosmos-rpc.publicnode.com:443",
        explorer_url="https://www.mintscan.io/cosmos",
        coin_type=118,
    ),
    
    # --- Polkadot Ecosystem ---
    "polkadot": ChainConfig(
        chain_id="polkadot",
        name="Polkadot",
        symbol="DOT",
        chain_type=ChainType.WASM,
        signing_curve=SigningCurve.EDDSA_ED25519,
        address_format=AddressFormat.SS58,
        decimals=10,
        rpc_env_var="WHALE_POLKADOT_RPC",
        default_rpc="wss://rpc.polkadot.io",
        explorer_url="https://polkadot.subscan.io",
        coin_type=354,
    ),
    
    # --- Cardano ---
    "cardano": ChainConfig(
        chain_id="cardano",
        name="Cardano",
        symbol="ADA",
        chain_type=ChainType.CUSTOM,
        signing_curve=SigningCurve.EDDSA_ED25519,
        address_format=AddressFormat.BECH32,
        decimals=6,
        rpc_env_var="WHALE_CARDANO_RPC",
        default_rpc="https://cardano-mainnet.blockfrost.io/api/v0",
        explorer_url="https://cardanoscan.io",
        coin_type=1815,
    ),
    
    # --- TRON ---
    "tron": ChainConfig(
        chain_id="tron",
        name="TRON",
        symbol="TRX",
        chain_type=ChainType.CUSTOM,
        signing_curve=SigningCurve.ECDSA_SECP256K1,
        address_format=AddressFormat.BASE58,
        decimals=6,
        rpc_env_var="WHALE_TRON_RPC",
        default_rpc="https://api.trongrid.io",
        explorer_url="https://tronscan.org",
        coin_type=195,
    ),
    
    # --- TON ---
    "ton": ChainConfig(
        chain_id="ton",
        name="TON",
        symbol="TON",
        chain_type=ChainType.CUSTOM,
        signing_curve=SigningCurve.EDDSA_ED25519,
        address_format=AddressFormat.BASE58,
        decimals=9,
        rpc_env_var="WHALE_TON_RPC",
        default_rpc="https://toncenter.com/api/v2/jsonRPC",
        explorer_url="https://tonscan.org",
        coin_type=607,
    ),
    
    # --- Near Protocol ---
    "near": ChainConfig(
        chain_id="near",
        name="Near Protocol",
        symbol="NEAR",
        chain_type=ChainType.WASM,
        signing_curve=SigningCurve.EDDSA_ED25519,
        address_format=AddressFormat.CUSTOM,
        decimals=24,
        rpc_env_var="WHALE_NEAR_RPC",
        default_rpc="https://rpc.mainnet.near.org",
        explorer_url="https://nearblocks.io",
        coin_type=397,
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_chain(chain_key: str) -> Optional[ChainConfig]:
    """
    Get chain configuration by key.
    
    Args:
        chain_key: Chain identifier (e.g., 'ethereum', 'solana')
        
    Returns:
        ChainConfig if found, None otherwise
    """
    return CHAIN_REGISTRY.get(chain_key.lower())


def get_all_chains() -> list[ChainConfig]:
    """Get all supported chain configurations."""
    return list(CHAIN_REGISTRY.values())


def get_chains_by_curve(curve: SigningCurve) -> list[ChainConfig]:
    """
    Get all chains using a specific signing curve.
    
    Args:
        curve: SigningCurve to filter by
        
    Returns:
        List of ChainConfig entries using that curve
    """
    return [c for c in CHAIN_REGISTRY.values() if c.signing_curve == curve]


def get_evm_chains() -> list[ChainConfig]:
    """Get all EVM-compatible chains."""
    return [c for c in CHAIN_REGISTRY.values() if c.chain_type == ChainType.EVM]


def is_chain_supported(chain_key: str) -> bool:
    """Check if a chain is supported."""
    return chain_key.lower() in CHAIN_REGISTRY


def get_chain_by_id(chain_id: str) -> Optional[ChainConfig]:
    """
    Get chain configuration by chain ID.
    
    Args:
        chain_id: Numeric chain ID (for EVM) or string identifier
        
    Returns:
        ChainConfig if found, None otherwise
    """
    for config in CHAIN_REGISTRY.values():
        if config.chain_id == chain_id:
            return config
    return None


# =============================================================================
# CHAIN STATISTICS
# =============================================================================

CHAIN_STATS = {
    "total_chains": len(CHAIN_REGISTRY),
    "evm_chains": len(get_evm_chains()),
    "ecdsa_chains": len(get_chains_by_curve(SigningCurve.ECDSA_SECP256K1)),
    "eddsa_chains": len(get_chains_by_curve(SigningCurve.EDDSA_ED25519)),
    "supported_symbols": list(set(c.symbol for c in CHAIN_REGISTRY.values())),
}
