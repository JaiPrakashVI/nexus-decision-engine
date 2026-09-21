-- NEXUS Database Initialization & TimescaleDB Extension
-- Enables TimescaleDB hypertable partitioning on time-series telemetry.

CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Devices Table
CREATE TABLE IF NOT EXISTS devices (
    id VARCHAR(64) PRIMARY KEY,
    device_type VARCHAR(32) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    registered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    meta_info JSONB
);

-- Telemetry Table
CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL,
    device_id VARCHAR(64) NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    sequence_number BIGINT NOT NULL,
    trace_id VARCHAR(64) NOT NULL,
    pressure_psi DOUBLE PRECISION NOT NULL,
    flow_rate_gpm DOUBLE PRECISION NOT NULL,
    temperature_c DOUBLE PRECISION NOT NULL,
    vibration_rms DOUBLE PRECISION DEFAULT 0.0,
    power_kw DOUBLE PRECISION DEFAULT 0.0,
    battery_pct DOUBLE PRECISION DEFAULT 100.0,
    reconstructed BOOLEAN DEFAULT FALSE,
    confidence DOUBLE PRECISION DEFAULT 1.0,
    PRIMARY KEY (timestamp, id)
);

-- Convert telemetry table into a TimescaleDB hypertable partitioned by timestamp (7 day chunks)
SELECT create_hypertable('telemetry', 'timestamp', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_telemetry_device_time ON telemetry (device_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_trace ON telemetry (trace_id);

-- State Snapshots Table
CREATE TABLE IF NOT EXISTS state_snapshots (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    node_id VARCHAR(64) NOT NULL,
    operational_state VARCHAR(32) NOT NULL,
    state_source VARCHAR(16) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    divergence_score DOUBLE PRECISION DEFAULT 0.0,
    state_details JSONB
);
CREATE INDEX IF NOT EXISTS idx_snapshots_node_time ON state_snapshots (node_id, timestamp DESC);

-- Anomalies Table
CREATE TABLE IF NOT EXISTS anomalies (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    anomaly_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    detector VARCHAR(32) NOT NULL,
    metrics_snapshot JSONB
);
CREATE INDEX IF NOT EXISTS idx_anomalies_device_time ON anomalies (device_id, timestamp DESC);

-- Missing Events Table
CREATE TABLE IF NOT EXISTS missing_events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    expected_transition VARCHAR(128) NOT NULL,
    observed_transition VARCHAR(128) NOT NULL,
    unexplained_latency_ms DOUBLE PRECISION DEFAULT 0.0,
    confidence DOUBLE PRECISION DEFAULT 0.5,
    details JSONB
);

-- Incidents Table
CREATE TABLE IF NOT EXISTS incidents (
    id VARCHAR(64) PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    title VARCHAR(256) NOT NULL,
    root_cause_node VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    status VARCHAR(16) DEFAULT 'OPEN',
    affected_nodes JSONB NOT NULL,
    resolved_at TIMESTAMPTZ
);

-- Interventions Table
CREATE TABLE IF NOT EXISTS interventions (
    id VARCHAR(64) PRIMARY KEY,
    incident_id VARCHAR(64) NOT NULL REFERENCES incidents(id),
    timestamp TIMESTAMPTZ NOT NULL,
    proposed_by VARCHAR(32) NOT NULL,
    action_name VARCHAR(64) NOT NULL,
    target_nodes JSONB NOT NULL,
    parameters JSONB,
    simulated_recovery_time_sec DOUBLE PRECISION NOT NULL,
    actual_recovery_time_sec DOUBLE PRECISION,
    constraints_passed BOOLEAN DEFAULT TRUE
);

-- Experiments Table
CREATE TABLE IF NOT EXISTS experiments (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    random_seed INTEGER NOT NULL,
    loss_rate DOUBLE PRECISION NOT NULL,
    delay_ms INTEGER NOT NULL,
    noise_level VARCHAR(16) NOT NULL,
    config JSONB NOT NULL,
    metrics JSONB NOT NULL
);
