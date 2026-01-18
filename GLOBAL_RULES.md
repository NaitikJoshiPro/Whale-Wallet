# Whale Wallet - Global Rules & Configuration

> **Enterprise Production Guidelines for Sovereign Wealth Preservation**

This document defines the architectural invariants, policy defaults, and operational guidelines for the Whale Wallet system.

---

## 1. Architecture Invariants

### Security Principles

| Principle | Description |
|-----------|-------------|
| **Non-Custodial by Design** | All key shards remain under user control. Server shard runs in TEE and cannot sign alone. |
| **Zero Trust** | Every request is authenticated, validated, and policy-checked—even internal services. |
| **Defense in Depth** | Multiple security layers: TLS 1.3, TEE attestation, MPC threshold, policy engine. |
| **Fail Secure** | On any error or timeout, transactions are blocked, not approved. |

### MPC Configuration

```yaml
threshold: 2-of-3
shards:
  - user_mobile: Secure Enclave (iOS) / Titan M (Android)
  - server_cloud: AWS Nitro Enclave / GCP Confidential Space
  - recovery: Guardian shards / offline backup
```

---

## 2. Supported Blockchains

### Chain Registry (18 Chains)

| Chain | Symbol | Curve | Type | MPC Compatible |
|-------|--------|-------|------|----------------|
| Bitcoin | BTC | ECDSA secp256k1 | UTXO | ✅ |
| Ethereum | ETH | ECDSA secp256k1 | EVM | ✅ |
| Arbitrum | ETH | ECDSA secp256k1 | EVM | ✅ |
| Optimism | ETH | ECDSA secp256k1 | EVM | ✅ |
| Base | ETH | ECDSA secp256k1 | EVM | ✅ |
| Polygon | MATIC | ECDSA secp256k1 | EVM | ✅ |
| BNB Chain | BNB | ECDSA secp256k1 | EVM | ✅ |
| Avalanche | AVAX | ECDSA secp256k1 | EVM | ✅ |
| Fantom | FTM | ECDSA secp256k1 | EVM | ✅ |
| Solana | SOL | EdDSA Ed25519 | SVM | ✅ |
| Cosmos | ATOM | ECDSA secp256k1 | Tendermint | ✅ |
| Polkadot | DOT | EdDSA Ed25519 | Substrate | ✅ |
| Cardano | ADA | EdDSA Ed25519 | UTXO | ✅ |
| TRON | TRX | ECDSA secp256k1 | Custom | ✅ |
| TON | TON | EdDSA Ed25519 | Custom | ✅ |
| Near | NEAR | EdDSA Ed25519 | WASM | ✅ |
| Sui | SUI | EdDSA Ed25519 | Move | ✅ |
| Aptos | APT | EdDSA Ed25519 | Move | ✅ |

---

## 3. Policy Engine Defaults

### Velocity Limits by Tier

| Tier | Per-TX Max | Daily Max | 2FA Threshold | Swap Fee |
|------|------------|-----------|---------------|----------|
| **Orca** | $5,000 | $10,000 | $1,000 | 0.5% |
| **Humpback** | $100,000 | $500,000 | $10,000 | 0% |
| **Blue** | Unlimited | Unlimited | $100,000 | 0% |

### Default Policy Rules

```python
# All users start with these policies active:
VELOCITY_LIMIT = True       # Enforces daily/per-tx limits
WHITELIST_MODE = "warn"     # Warn on new addresses, but allow
TIME_LOCK_HOURS = 0         # No default time lock
GAS_PROTECTION = True       # Warn on high gas prices
CONTRACT_VERIFICATION = True # Block unverified contracts
DURESS_MODE = True          # Decoy wallet available
```

### Duress Mode Behavior

When `DURESS_PIN` is used:
1. Unlocks decoy wallet with nominal funds
2. All transactions are silently approved
3. Silent alert sent to emergency contacts
4. GPS coordinates logged (if available)

---

## 4. Rate Limiting

### API Rate Limits

| Endpoint Category | Orca | Humpback | Blue |
|-------------------|------|----------|------|
| **General API** | 100/min | 500/min | 2000/min |
| **Transaction Signing** | 10/min | 50/min | 200/min |
| **AI Concierge** | 20/hr | 100/hr | Unlimited |
| **Simulation** | 30/min | 150/min | 500/min |

### Burst Handling

- Short bursts (3x limit) allowed for 10 seconds
- Retry-After header provided on 429 responses
- Persistent abuse triggers temporary IP ban

---

## 5. Error Handling

### Circuit Breaker Pattern

```yaml
states:
  CLOSED: Normal operation
  OPEN: Service degraded, fail fast
  HALF_OPEN: Testing recovery

thresholds:
  failure_rate: 50%        # Trigger at 50% failures
  minimum_calls: 10        # Minimum calls before evaluation
  wait_duration: 30s       # Time in OPEN state
  permitted_calls: 5       # Calls allowed in HALF_OPEN
```

### Error Response Format

```json
{
  "error": {
    "code": "POLICY_VIOLATION",
    "message": "Transaction exceeds daily limit",
    "request_id": "req_abc123",
    "details": {
      "current_daily_usd": 45000,
      "limit_daily_usd": 50000,
      "transaction_usd": 10000
    }
  }
}
```

---

## 6. Deployment Checklist

### Pre-Production

- [ ] All secrets in Secret Manager (not env vars)
- [ ] TLS 1.3 only (no fallback)
- [ ] Rate limiting enabled
- [ ] Attestation enabled (mobile apps)
- [ ] Blowfish API key configured
- [ ] All chain RPCs configured
- [ ] Database connection pool sized
- [ ] Redis cluster configured
- [ ] Log aggregation enabled
- [ ] Health checks responding

### Post-Deployment

- [ ] Verify `/health` returns 200
- [ ] Verify `/health/ready` shows all services connected
- [ ] Test transaction simulation
- [ ] Test policy evaluation
- [ ] Verify rate limiting active
- [ ] Check structured logging output
- [ ] Verify CORS configuration
- [ ] Run smoke test suite

---

## 7. Environment Variables

### Required (Production)

```bash
WHALE_ENV=production
WHALE_DB_PASSWORD=<from-secret-manager>
WHALE_JWT_SECRET=<from-secret-manager>
WHALE_ENCRYPTION_KEY=<from-secret-manager>
WHALE_LLM_API_KEY=<from-secret-manager>
```

### Optional Chain RPCs

```bash
WHALE_ETHEREUM_RPC=https://eth-mainnet.g.alchemy.com/v2/...
WHALE_ARBITRUM_RPC=https://arb-mainnet.g.alchemy.com/v2/...
WHALE_BITCOIN_RPC=https://...
# ... etc
```

---

## 8. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-18 | Initial enterprise release with 18 chains |
