# Whale Wallet

> **Sovereign Wealth Preservation System for Digital Assets**

A non-custodial MPC wallet designed for high-net-worth individuals, combining institutional-grade security with personal sovereignty.

## 🐋 Overview

Whale Wallet resolves the "Custody Paradox" faced by crypto HNWIs—the choice between:
- **Retail chaos**: Hot wallets with connectivity but poor security
- **Institutional imprisonment**: Custody solutions with security but no sovereignty

**Whale Wallet provides both**: MPC-based security, programmable policy engine, inheritance planning, and white-glove support—all while remaining completely non-custodial.

## ✨ Key Features

### 🔐 Security
- **2-of-3 MPC Threshold Signing**: No single point of failure
- **Deep Duress Mode**: Decoy wallet for physical coercion scenarios
- **Policy Engine**: Velocity limits, whitelists, time locks
- **Transaction Simulation**: Preview effects before signing
- **Post-Quantum Ready**: Transport layer secured with CRYSTALS-Kyber

### 💰 Wealth Preservation
- **Sovereign Inheritance**: Dead Man's Switch with guardian shards
- **Personal CFO**: Rule-based transaction governance
- **Zero Swap Fees**: Membership model, not transaction friction

### 🤖 AI Concierge
- **Natural Language Support**: Ask anything about crypto
- **Transaction Analysis**: Risk assessment for any contract
- **Policy Recommendations**: AI-suggested security improvements

## 🏗 Architecture

```
┌─────────────────────────────────────────┐
│           Mobile App (iOS/Android)      │
│        ┌─────────────────────────┐      │
│        │    Secure Enclave       │      │
│        │      (Shard A)          │      │
│        └─────────────────────────┘      │
└─────────────────┬───────────────────────┘
                  │ TLS 1.3 + Noise Protocol
                  ▼
┌─────────────────────────────────────────┐
│         Cloud Run (FastAPI)             │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ API Gateway │  │  Policy Engine  │   │
│  └─────────────┘  └─────────────────┘   │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ AI Concierge│  │ Tx Simulator    │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│     TEE (AWS Nitro / GCP Confidential)  │
│        ┌─────────────────────────┐      │
│        │      Shard B Storage    │      │
│        │      + MPC Signing      │      │
│        └─────────────────────────┘      │
└─────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Anthropic API key (for AI features)

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/whale-wallet.git
cd whale-wallet

# Copy environment file
cp .env.example .env

# Edit .env with your API keys
vim .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# API is now running at http://localhost:8080
# Docs at http://localhost:8080/docs (development only)
```

### Without Docker

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database (requires PostgreSQL)
# Edit .env with your database credentials
alembic upgrade head

# Run the server
uvicorn app.main:app --reload --port 8080
```

## 📁 Project Structure

```
whale-wallet/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Configuration management
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py      # Authentication endpoints
│   │       ├── wallet.py    # Wallet operations
│   │       ├── policy.py    # Policy CRUD
│   │       ├── transaction.py # Transaction signing
│   │       └── concierge.py # AI concierge
│   ├── core/
│   │   ├── events.py        # Lifecycle handlers
│   │   └── middleware.py    # Custom middleware
│   ├── policy_engine/
│   │   ├── executor.py      # Rule execution engine
│   │   └── rules/           # Rule implementations
│   └── ai/
│       ├── concierge.py     # Main AI service
│       ├── agents/          # Specialist agents
│       ├── memory/          # Short/long-term memory
│       └── prompts/         # System prompts
├── infrastructure/
│   └── init.sql             # Database schema
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/token` - Get access token
- `GET /api/v1/auth/me` - Get current user

### Wallet
- `GET /api/v1/wallet/overview` - Portfolio overview
- `GET /api/v1/wallet/addresses` - Wallet addresses
- `GET /api/v1/wallet/mpc/status` - MPC shard status

### Policies
- `GET /api/v1/policies` - List policies
- `POST /api/v1/policies` - Create policy
- `POST /api/v1/policies/evaluate` - Dry-run evaluation

### Transactions
- `POST /api/v1/transactions` - Create transaction
- `POST /api/v1/transactions/simulate` - Simulate transaction
- `POST /api/v1/transactions/{id}/sign` - Sign and broadcast

### AI Concierge
- `POST /api/v1/concierge/chat` - Chat with AI
- `POST /api/v1/concierge/analyze/transaction` - Analyze transaction

## 💎 Membership Tiers

| Tier | Annual Fee | Swap Fee | Features |
|------|-----------|----------|----------|
| **Orca** | Free | 0.5% | Basic MPC, standard policies |
| **Humpback** | $1,000 | 0% | Advanced policies, inheritance, MEV protection |
| **Blue** | $10,000 | 0% | 24/7 concierge, custom logic, insurance |

## 🔒 Security Model

### Multi-Party Computation (MPC)
- Keys are never stored in one location
- 2-of-3 threshold required to sign
- Shards: Mobile (user) + Server (TEE) + Recovery (guardians)

### Trusted Execution Environment (TEE)
- Server shard runs in AWS Nitro / GCP Confidential Space
- Even Whale Wallet admins cannot access keys
- Cryptographic attestation verifies code integrity

### Policy Engine
- All policies enforced server-side in TEE
- User cannot bypass their own rules under duress
- Comprehensive audit trail

## 🛣 Roadmap

- [x] Core MPC architecture
- [x] Policy engine framework
- [x] AI concierge integration
- [ ] Mobile app (iOS/Android)
- [ ] Hardware wallet integration (air-gap mode)
- [ ] Post-quantum signatures
- [ ] Decentralized guardian network

## 📄 License

Proprietary - All rights reserved.

## 🤝 Support

For Blue tier members: Use in-app concierge for 24/7 support.

For all users: support@whalewallet.io
