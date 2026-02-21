-- ================================================
-- ATIS - PostgreSQL Database Schema
-- ================================================

-- Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fuzzy text search

-- ================================
-- User Management
-- ================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    preferences JSONB DEFAULT '{}'::jsonb,
    alert_settings JSONB DEFAULT '{
        "email_alerts": true,
        "push_notifications": true,
        "critical_threshold": 0.9,
        "high_threshold": 0.7
    }'::jsonb
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- ================================
-- Personal Watchlists
-- ================================

CREATE TABLE watchlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    spkid VARCHAR(50) NOT NULL,
    name VARCHAR(255),
    notes TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    UNIQUE(user_id, spkid)
);

CREATE INDEX idx_watchlists_user ON watchlists(user_id);
CREATE INDEX idx_watchlists_spkid ON watchlists(spkid);
CREATE INDEX idx_watchlists_priority ON watchlists(priority);

-- ================================
-- Alert History
-- ================================

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL, -- critical_threshold, threat_increase, anomaly, system
    level VARCHAR(20) NOT NULL, -- critical, high, warning, medium, info
    spkid VARCHAR(50),
    object_name VARCHAR(255),
    threat_score DECIMAL(5,4),
    previous_score DECIMAL(5,4),
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by UUID REFERENCES users(id)
);

CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_level ON alerts(level);
CREATE INDEX idx_alerts_spkid ON alerts(spkid);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX idx_alerts_metadata ON alerts USING GIN(metadata);

-- ================================
-- User Alert Subscriptions
-- ================================

CREATE TABLE user_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    alert_id UUID REFERENCES alerts(id) ON DELETE CASCADE,
    read_at TIMESTAMP WITH TIME ZONE,
    dismissed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, alert_id)
);

CREATE INDEX idx_user_alerts_user ON user_alerts(user_id);
CREATE INDEX idx_user_alerts_alert ON user_alerts(alert_id);
CREATE INDEX idx_user_alerts_read ON user_alerts(read_at);

-- ================================
-- Threat Snapshots (Historical Data)
-- ================================

CREATE TABLE threat_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_objects INTEGER,
    avg_threat DECIMAL(5,4),
    max_threat DECIMAL(5,4),
    critical_count INTEGER,
    high_count INTEGER,
    medium_count INTEGER,
    low_count INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_snapshots_time ON threat_snapshots(snapshot_time DESC);

-- ================================
-- Threat Time Series Data
-- ================================

CREATE TABLE threat_timeseries (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id UUID REFERENCES threat_snapshots(id) ON DELETE CASCADE,
    spkid VARCHAR(50) NOT NULL,
    object_name VARCHAR(255),
    threat_score DECIMAL(5,4) NOT NULL,
    moid DECIMAL(10,6),
    h_magnitude DECIMAL(6,2),
    diameter DECIMAL(10,2),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_timeseries_snapshot ON threat_timeseries(snapshot_id);
CREATE INDEX idx_timeseries_spkid ON threat_timeseries(spkid);
CREATE INDEX idx_timeseries_recorded ON threat_timeseries(recorded_at DESC);
CREATE INDEX idx_timeseries_spkid_time ON threat_timeseries(spkid, recorded_at DESC);

-- ================================
-- API Usage Tracking
-- ================================

CREATE TABLE api_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_usage_user ON api_usage(user_id);
CREATE INDEX idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX idx_api_usage_created ON api_usage(created_at DESC);

-- ================================
-- Session Management
-- ================================

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- ================================
-- Audit Log
-- ================================

CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);

-- ================================
-- Functions and Triggers
-- ================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Clean old sessions trigger
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS VOID AS $$
BEGIN
    DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP AND revoked_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- ================================
-- Initial Admin User (Change Password!)
-- ================================

INSERT INTO users (email, password_hash, full_name, is_admin)
VALUES (
    'admin@atis.local',
    -- Password: 'admin123' (CHANGE THIS IN PRODUCTION!)
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aqaL3VYdVUNe',
    'System Administrator',
    true
);

-- ================================
-- Sample Data (Development Only)
-- ================================

-- Sample users
INSERT INTO users (email, password_hash, full_name) VALUES
    ('user1@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aqaL3VYdVUNe', 'John Doe'),
    ('user2@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aqaL3VYdVUNe', 'Jane Smith');

COMMIT;
