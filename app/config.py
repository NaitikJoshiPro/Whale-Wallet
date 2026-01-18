"""
Whale Wallet Configuration Module

Centralized configuration using Pydantic Settings for type-safe
environment variable management with validation.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings are validated at startup. Missing required settings
    will cause the application to fail fast with clear error messages.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="WHALE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # === Core Configuration ===
    env: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    api_port: int = Field(default=8080, ge=1, le=65535)
    api_host: str = "0.0.0.0"
    debug: bool = False
    
    # === Database ===
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "whale_wallet"
    db_user: str = "whale_api"
    db_password: SecretStr = Field(...)
    
    @property
    def database_url(self) -> str:
        """Construct async database URL for SQLAlchemy."""
        password = self.db_password.get_secret_value()
        return f"postgresql+asyncpg://{self.db_user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def database_url_sync(self) -> str:
        """Construct sync database URL for Alembic migrations."""
        password = self.db_password.get_secret_value()
        return f"postgresql://{self.db_user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # === Redis ===
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # === MPC Configuration ===
    mpc_node_id: str = "local-dev"
    mpc_threshold: int = Field(default=2, ge=1)
    mpc_parties: int = Field(default=3, ge=2)
    tee_attestation_url: str | None = None
    
    @field_validator("mpc_threshold")
    @classmethod
    def validate_threshold(cls, v: int, info) -> int:
        """Ensure threshold is valid for MPC scheme."""
        parties = info.data.get("mpc_parties", 3)
        if v > parties:
            raise ValueError(f"Threshold ({v}) cannot exceed parties ({parties})")
        return v
    
    # === AI Layer ===
    llm_provider: Literal["anthropic", "openai", "vertex"] = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"
    llm_api_key: SecretStr = Field(...)
    openai_api_key: SecretStr | None = None
    
    # === Vector Database ===
    vector_db_provider: Literal["pinecone", "chromadb", "none"] = "pinecone"
    pinecone_api_key: SecretStr | None = None
    pinecone_environment: str = "us-east-1"
    pinecone_index: str = "whale-memory"
    
    # === External APIs ===
    blowfish_api_key: SecretStr | None = None
    alchemy_api_key: SecretStr | None = None
    
    # === Multi-Chain RPC Endpoints ===
    # EVM Chains
    ethereum_rpc: str = "https://eth.llamarpc.com"
    arbitrum_rpc: str = "https://arb1.arbitrum.io/rpc"
    optimism_rpc: str = "https://mainnet.optimism.io"
    base_rpc: str = "https://mainnet.base.org"
    polygon_rpc: str = "https://polygon-rpc.com"
    bsc_rpc: str = "https://bsc-dataseed.binance.org"
    avalanche_rpc: str = "https://api.avax.network/ext/bc/C/rpc"
    fantom_rpc: str = "https://rpc.ftm.tools"
    
    # Non-EVM Chains
    bitcoin_rpc: str = "https://btc.llamarpc.com"
    solana_rpc: str = "https://api.mainnet-beta.solana.com"
    cosmos_rpc: str = "https://cosmos-rpc.publicnode.com:443"
    polkadot_rpc: str = "wss://rpc.polkadot.io"
    cardano_rpc: str = "https://cardano-mainnet.blockfrost.io/api/v0"
    tron_rpc: str = "https://api.trongrid.io"
    ton_rpc: str = "https://toncenter.com/api/v2/jsonRPC"
    near_rpc: str = "https://rpc.mainnet.near.org"
    sui_rpc: str = "https://fullnode.mainnet.sui.io"
    aptos_rpc: str = "https://fullnode.mainnet.aptoslabs.com/v1"
    

    # === Security ===
    jwt_secret: SecretStr = Field(...)
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = Field(default=60, ge=5)
    encryption_key: SecretStr = Field(...)
    
    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: SecretStr) -> SecretStr:
        """Ensure JWT secret is sufficiently long."""
        if len(v.get_secret_value()) < 32:
            raise ValueError("JWT secret must be at least 32 characters")
        return v
    
    # === Rate Limiting ===
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    
    # === Feature Flags ===
    enable_duress_mode: bool = True
    enable_inheritance: bool = True
    enable_ai_concierge: bool = True
    attestation_enabled: bool = False
    
    # === Membership Tiers ===
    @property
    def tier_limits(self) -> dict:
        """Define limits per membership tier."""
        return {
            "orca": {
                "daily_tx_limit_usd": 10_000,
                "advanced_policies": False,
                "concierge": False,
                "swap_fee_percent": 0.5
            },
            "humpback": {
                "daily_tx_limit_usd": 500_000,
                "advanced_policies": True,
                "concierge": False,
                "swap_fee_percent": 0.0
            },
            "blue": {
                "daily_tx_limit_usd": float("inf"),
                "advanced_policies": True,
                "concierge": True,
                "swap_fee_percent": 0.0
            }
        }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once
    and reused across the application lifetime.
    """
    return Settings()
