"""
API Integration Tests

Tests the full API request/response cycle including:
- Health checks
- Authentication flow
- Policy CRUD
- Transaction flow
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Basic health check should return 200."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_liveness_probe(self, client: TestClient):
        """Liveness probe should return 200."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
    
    def test_readiness_probe(self, client: TestClient):
        """Readiness probe should check dependencies."""
        response = client.get("/health/ready")
        
        assert response.status_code in [200, 503]
        data = response.json()
        assert "database" in data
        assert "redis" in data


class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    def test_register_user(self, client: TestClient):
        """User registration should return user ID."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "device_id": "a" * 32
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert data["tier"] == "orca"
    
    def test_login_returns_token(self, client: TestClient):
        """Login should return JWT token."""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestPolicyEndpoints:
    """Tests for policy CRUD endpoints."""
    
    def test_list_policies(self, client: TestClient, auth_headers: dict):
        """Should list all policies for user."""
        response = client.get(
            "/api/v1/policies",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_policy(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_policy: dict
    ):
        """Should create a new policy."""
        response = client.post(
            "/api/v1/policies",
            json=sample_policy,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_policy["name"]
        assert data["rule_type"] == sample_policy["rule_type"]
    
    def test_evaluate_policy(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Should dry-run policy evaluation."""
        response = client.post(
            "/api/v1/policies/evaluate",
            json={
                "chain": "ethereum",
                "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f8fE89",
                "value_usd": 5000
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "allowed" in data


class TestTransactionEndpoints:
    """Tests for transaction endpoints."""
    
    def test_create_transaction(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_transaction: dict
    ):
        """Should create a new transaction."""
        response = client.post(
            "/api/v1/transactions",
            json=sample_transaction,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert "simulation" in data
    
    def test_simulate_transaction(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_transaction: dict
    ):
        """Should simulate transaction effects."""
        response = client.post(
            "/api/v1/transactions/simulate",
            json=sample_transaction,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "risk_level" in data
        assert "balance_changes" in data
    
    def test_get_transaction_history(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Should return transaction history."""
        response = client.get(
            "/api/v1/transactions/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
