"""
Test Configuration and Fixtures

Shared fixtures for all tests including:
- Mock database sessions
- Test client
- Authentication helpers
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import Settings


# Override settings for testing
def get_test_settings() -> Settings:
    """Get settings configured for testing."""
    return Settings(
        env="development",
        db_host="localhost",
        db_password="testpassword",  # type: ignore
        jwt_secret="test-jwt-secret-minimum-32-characters",  # type: ignore
        encryption_key="test-encryption-key-32-bytes-xx",  # type: ignore
        llm_api_key="test-api-key",  # type: ignore
        enable_ai_concierge=False,  # Disable AI in tests
        attestation_enabled=False
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator:
    """Create a synchronous test client."""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict:
    """Get authentication headers for testing."""
    # In production tests, this would generate a real JWT
    return {
        "Authorization": "Bearer test-token",
        "X-Request-ID": "test-request-123"
    }


@pytest.fixture
def sample_policy() -> dict:
    """Sample policy for testing."""
    return {
        "rule_type": "velocity",
        "name": "Test Velocity Limit",
        "description": "Test policy for unit tests",
        "config": {
            "max_daily_usd": 10000,
            "max_per_tx_usd": 5000,
            "require_2fa_above_usd": 1000
        },
        "priority": 10,
        "is_active": True
    }


@pytest.fixture
def sample_transaction() -> dict:
    """Sample transaction for testing."""
    return {
        "chain": "ethereum",
        "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f8fE89",
        "value": "1000000000000000000",  # 1 ETH in wei
        "data": None,
        "recipient_label": "Test Recipient"
    }
