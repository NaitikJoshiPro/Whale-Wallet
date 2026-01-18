-- Whale Wallet Database Initialization Script
-- Run on first database creation

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tier VARCHAR(20) NOT NULL DEFAULT 'orca' CHECK (tier IN ('orca', 'humpback', 'blue')),
    email VARCHAR(255),
    device_id VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ,
    duress_mode_active BOOLEAN DEFAULT FALSE,
    inheritance_triggered BOOLEAN DEFAULT FALSE
);

-- MPC Shard Metadata (Never store actual shards here)
CREATE TABLE IF NOT EXISTS shard_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    shard_type VARCHAR(10) CHECK (shard_type IN ('mobile', 'server', 'recovery')),
    enclave_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rotated_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

-- Policy Engine Rules
CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rule_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    rule_config JSONB NOT NULL,
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Whitelist Addresses
CREATE TABLE IF NOT EXISTS whitelists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    chain VARCHAR(20) NOT NULL,
    address VARCHAR(255) NOT NULL,
    label VARCHAR(100),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, chain, address)
);

-- Inheritance Configuration
CREATE TABLE IF NOT EXISTS inheritance_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    inactivity_threshold_days INT DEFAULT 180,
    guardians JSONB,
    last_ping_at TIMESTAMPTZ DEFAULT NOW(),
    triggered_at TIMESTAMPTZ
);

-- Transaction Log (Immutable Audit Trail)
CREATE TABLE IF NOT EXISTS transaction_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    chain VARCHAR(20) NOT NULL,
    tx_hash VARCHAR(255),
    action VARCHAR(50),
    amount_usd DECIMAL(20, 2),
    destination VARCHAR(255),
    policy_result JSONB,
    simulation_result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversation History for AI Concierge
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    messages JSONB DEFAULT '[]',
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

-- API Keys for external services (encrypted)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    service VARCHAR(50) NOT NULL,
    key_encrypted BYTEA NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- Create Indices for Performance
CREATE INDEX IF NOT EXISTS idx_policies_user ON policies(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_policies_type ON policies(rule_type);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transaction_log(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inheritance_ping ON inheritance_config(last_ping_at);
CREATE INDEX IF NOT EXISTS idx_whitelists_user ON whitelists(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, last_activity DESC);

-- Insert demo user for development
INSERT INTO users (id, tier, email, device_id)
VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'blue',
    'demo@whalewallet.io',
    'demo-device-abc123def456'
) ON CONFLICT DO NOTHING;

-- Insert demo policies
INSERT INTO policies (user_id, rule_type, name, description, rule_config, priority)
VALUES 
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'velocity', 'Daily Spending Limit', 
     'Limit daily outflow to $50,000', 
     '{"max_daily_usd": 50000, "max_per_tx_usd": 25000, "require_2fa_above_usd": 10000}', 10),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'timelock', 'Night Block',
     'Block large transfers between 11 PM and 6 AM',
     '{"block_start_hour": 23, "block_end_hour": 6, "timezone": "America/New_York"}', 20),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'whitelist', 'Known Addresses',
     'Warn on transfers to unknown addresses',
     '{"mode": "warn_unknown", "require_2fa_for_new": true, "quarantine_hours_for_new": 24}', 5)
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO whale_api;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO whale_api;

COMMENT ON TABLE users IS 'Core user accounts for Whale Wallet';
COMMENT ON TABLE policies IS 'Policy engine rules that govern transaction signing';
COMMENT ON TABLE transaction_log IS 'Immutable audit trail of all transaction attempts';
