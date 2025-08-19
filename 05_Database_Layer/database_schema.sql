-- ============================================================================
-- ADAPTIVE MIND - PostgreSQL Schema Design for BiasLedger Persistence
-- Session 6: Database Layer Implementation
-- Enterprise-Grade Production Schema
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create dedicated schema for Adaptive Mind
CREATE SCHEMA IF NOT EXISTS adaptive_mind;
SET search_path TO adaptive_mind, public;

-- ============================================================================
-- CORE TABLES: Framework Infrastructure
-- ============================================================================

-- Providers table: Track all AI service providers
CREATE TABLE providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    provider_type VARCHAR(50) NOT NULL, -- 'openai', 'anthropic', 'azure', 'gemini'
    base_url TEXT,
    api_version VARCHAR(20),
    rate_limit_rpm INTEGER DEFAULT 60,
    rate_limit_tpm INTEGER DEFAULT 40000,
    cost_per_1k_tokens DECIMAL(10,6),
    max_context_length INTEGER DEFAULT 4096,
    supports_streaming BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Models table: Track specific models within providers
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    model_identifier VARCHAR(200) NOT NULL, -- API model string
    max_tokens INTEGER DEFAULT 4096,
    supports_functions BOOLEAN DEFAULT false,
    supports_vision BOOLEAN DEFAULT false,
    cost_input_per_1k DECIMAL(10,6),
    cost_output_per_1k DECIMAL(10,6),
    is_active BOOLEAN DEFAULT true,
    capabilities JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider_id, model_identifier)
);

-- ============================================================================
-- BIAS LEDGER: Core Audit and Bias Tracking
-- ============================================================================

-- Sessions table: Track interaction sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_type VARCHAR(50) NOT NULL, -- 'query', 'conversation', 'batch'
    user_identifier VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    total_requests INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0.00,
    success_rate DECIMAL(5,4) DEFAULT 1.0000,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Queries table: Individual query attempts
CREATE TABLE queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    query_hash VARCHAR(64) NOT NULL, -- SHA-256 hash for deduplication
    original_query TEXT NOT NULL,
    processed_query TEXT,
    query_category VARCHAR(100),
    complexity_score DECIMAL(3,2) DEFAULT 0.00,
    tokens_in_query INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX(query_hash),
    INDEX(session_id, created_at)
);

-- Attempts table: Individual provider attempts
CREATE TABLE attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id UUID NOT NULL REFERENCES queries(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES models(id),
    attempt_number INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL, -- 'success', 'failure', 'timeout', 'rate_limited'
    response_text TEXT,
    response_metadata JSONB DEFAULT '{}',

    -- Performance metrics
    latency_ms INTEGER,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_usd DECIMAL(8,6) DEFAULT 0.000000,

    -- Quality metrics
    quality_score DECIMAL(3,2),
    confidence_score DECIMAL(3,2),
    relevance_score DECIMAL(3,2),
    completeness_score DECIMAL(3,2),

    -- Error handling
    error_type VARCHAR(100),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Bias detection
    bias_indicators JSONB DEFAULT '{}',
    bias_score DECIMAL(3,2) DEFAULT 0.00,

    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX(query_id, attempt_number),
    INDEX(model_id, created_at),
    INDEX(status, created_at)
);

-- ============================================================================
-- LEARNING ENGINE: Performance and Adaptation Data
-- ============================================================================

-- Provider Performance table: Aggregated performance metrics
CREATE TABLE provider_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id),
    metric_date DATE NOT NULL,

    -- Volume metrics
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,

    -- Performance metrics
    avg_latency_ms DECIMAL(8,2),
    p95_latency_ms DECIMAL(8,2),
    avg_tokens_per_request DECIMAL(8,2),

    -- Quality metrics
    avg_quality_score DECIMAL(3,2),
    avg_bias_score DECIMAL(3,2),
    user_satisfaction_score DECIMAL(3,2),

    -- Cost metrics
    total_cost_usd DECIMAL(10,4),
    cost_per_request DECIMAL(8,6),
    cost_efficiency_score DECIMAL(3,2),

    -- Rankings
    quality_rank INTEGER,
    speed_rank INTEGER,
    cost_rank INTEGER,
    overall_rank INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(model_id, metric_date),
    INDEX(metric_date, overall_rank)
);

-- Learning patterns: Track what the system learns
CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type VARCHAR(100) NOT NULL, -- 'query_optimization', 'provider_selection', 'bias_detection'
    pattern_data JSONB NOT NULL,
    confidence_level DECIMAL(3,2) DEFAULT 0.00,
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4) DEFAULT 0.0000,
    learned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,

    INDEX(pattern_type, confidence_level DESC),
    INDEX(learned_at)
);

-- ============================================================================
-- TIME SERIES: Telemetry and Monitoring Data
-- ============================================================================

-- Telemetry Events: Real-time system events
CREATE TABLE telemetry_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    event_topic VARCHAR(100) NOT NULL,
    source_component VARCHAR(100) NOT NULL,

    -- Event data
    event_data JSONB NOT NULL DEFAULT '{}',
    correlation_id UUID,
    parent_event_id UUID REFERENCES telemetry_events(id),

    -- Metrics
    duration_ms INTEGER,
    memory_usage_mb DECIMAL(8,2),
    cpu_usage_percent DECIMAL(5,2),

    -- Context
    session_id UUID REFERENCES sessions(id),
    query_id UUID REFERENCES queries(id),
    attempt_id UUID REFERENCES attempts(id),

    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX(event_type, timestamp),
    INDEX(correlation_id),
    INDEX(session_id, timestamp)
);

-- System Metrics: Aggregated system performance
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Framework performance
    framework_overhead_ms DECIMAL(6,3) DEFAULT 0.000,
    active_sessions INTEGER DEFAULT 0,
    queries_per_minute INTEGER DEFAULT 0,

    -- Resource usage
    memory_usage_mb DECIMAL(8,2),
    cpu_usage_percent DECIMAL(5,2),
    disk_usage_mb DECIMAL(10,2),

    -- Provider health
    healthy_providers INTEGER DEFAULT 0,
    degraded_providers INTEGER DEFAULT 0,
    failed_providers INTEGER DEFAULT 0,

    -- Quality metrics
    overall_quality_score DECIMAL(3,2),
    bias_detection_rate DECIMAL(5,4),
    user_satisfaction DECIMAL(3,2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX(metric_timestamp)
);

-- ============================================================================
-- CONFIGURATION AND CACHE
-- ============================================================================

-- Configuration table: System settings
CREATE TABLE configuration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(200) NOT NULL UNIQUE,
    config_value JSONB NOT NULL,
    config_type VARCHAR(50) NOT NULL, -- 'framework', 'provider', 'bias_detection', 'learning'
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX(config_type, is_active)
);

-- Cache table: Response and computation cache
CREATE TABLE response_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 hash
    query_signature VARCHAR(64) NOT NULL,
    cached_response JSONB NOT NULL,
    model_id UUID REFERENCES models(id),

    -- Cache metadata
    hit_count INTEGER DEFAULT 0,
    quality_score DECIMAL(3,2),
    cache_size_bytes INTEGER,

    -- Expiration
    expires_at TIMESTAMP WITH TIME ZONE,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX(query_signature),
    INDEX(expires_at),
    INDEX(last_accessed_at)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Composite indexes for common query patterns
CREATE INDEX idx_attempts_performance ON attempts(model_id, status, created_at) WHERE status = 'success';
CREATE INDEX idx_attempts_bias_detection ON attempts(bias_score, created_at) WHERE bias_score > 0.00;
CREATE INDEX idx_queries_complexity ON queries(complexity_score DESC, created_at);
CREATE INDEX idx_telemetry_correlation ON telemetry_events(correlation_id, timestamp) WHERE correlation_id IS NOT NULL;
CREATE INDEX idx_provider_performance_ranking ON provider_performance(metric_date, overall_rank);

-- Partial indexes for active records
CREATE INDEX idx_providers_active ON providers(name) WHERE is_active = true;
CREATE INDEX idx_models_active ON models(provider_id, name) WHERE is_active = true;
CREATE INDEX idx_learning_patterns_active ON learning_patterns(pattern_type, confidence_level DESC) WHERE is_active = true;

-- GIN indexes for JSONB searches
CREATE INDEX idx_attempts_response_metadata_gin ON attempts USING GIN(response_metadata);
CREATE INDEX idx_attempts_bias_indicators_gin ON attempts USING GIN(bias_indicators);
CREATE INDEX idx_telemetry_events_data_gin ON telemetry_events USING GIN(event_data);
CREATE INDEX idx_learning_patterns_data_gin ON learning_patterns USING GIN(pattern_data);

-- ============================================================================
-- TRIGGERS AND FUNCTIONS
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_providers_updated_at BEFORE UPDATE ON providers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_models_updated_at BEFORE UPDATE ON models FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_configuration_updated_at BEFORE UPDATE ON configuration FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_provider_performance_updated_at BEFORE UPDATE ON provider_performance FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Session aggregation trigger
CREATE OR REPLACE FUNCTION update_session_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE sessions
        SET total_requests = total_requests + 1,
            total_tokens_used = total_tokens_used + COALESCE(NEW.tokens_input, 0) + COALESCE(NEW.tokens_output, 0),
            total_cost = total_cost + COALESCE(NEW.cost_usd, 0)
        WHERE id = (SELECT session_id FROM queries WHERE id = NEW.query_id);
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

CREATE TRIGGER update_session_stats_trigger AFTER INSERT ON attempts FOR EACH ROW EXECUTE FUNCTION update_session_stats();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Provider performance dashboard view
CREATE VIEW provider_dashboard AS
SELECT
    p.name as provider_name,
    m.name as model_name,
    pp.metric_date,
    pp.total_requests,
    pp.successful_requests,
    ROUND(pp.successful_requests * 100.0 / NULLIF(pp.total_requests, 0), 2) as success_rate_percent,
    pp.avg_latency_ms,
    pp.avg_quality_score,
    pp.avg_bias_score,
    pp.total_cost_usd,
    pp.overall_rank
FROM provider_performance pp
JOIN models m ON pp.model_id = m.id
JOIN providers p ON m.provider_id = p.id
WHERE pp.metric_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY pp.metric_date DESC, pp.overall_rank ASC;

-- Real-time system health view
CREATE VIEW system_health AS
SELECT
    sm.metric_timestamp,
    sm.framework_overhead_ms,
    sm.active_sessions,
    sm.queries_per_minute,
    sm.memory_usage_mb,
    sm.cpu_usage_percent,
    sm.healthy_providers,
    sm.degraded_providers,
    sm.failed_providers,
    sm.overall_quality_score,
    sm.bias_detection_rate,
    CASE
        WHEN sm.failed_providers = 0 AND sm.degraded_providers = 0 THEN 'HEALTHY'
        WHEN sm.failed_providers = 0 AND sm.degraded_providers < 3 THEN 'DEGRADED'
        ELSE 'CRITICAL'
    END as system_status
FROM system_metrics sm
WHERE sm.metric_timestamp >= NOW() - INTERVAL '1 hour'
ORDER BY sm.metric_timestamp DESC;

-- Bias detection summary view
CREATE VIEW bias_detection_summary AS
SELECT
    DATE(a.created_at) as detection_date,
    COUNT(*) as total_attempts,
    COUNT(*) FILTER (WHERE a.bias_score > 0.00) as biased_responses,
    ROUND(AVG(a.bias_score), 3) as avg_bias_score,
    MAX(a.bias_score) as max_bias_score,
    COUNT(DISTINCT a.model_id) as models_tested,
    ROUND(COUNT(*) FILTER (WHERE a.bias_score > 0.00) * 100.0 / COUNT(*), 2) as bias_detection_rate
FROM attempts a
WHERE a.status = 'success'
    AND a.created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(a.created_at)
ORDER BY detection_date DESC;

-- ============================================================================
-- INITIAL CONFIGURATION DATA
-- ============================================================================

-- Insert default configuration
INSERT INTO configuration (config_key, config_value, config_type, description) VALUES
('framework.max_concurrent_requests', '100', 'framework', 'Maximum concurrent requests to handle'),
('framework.default_timeout_ms', '30000', 'framework', 'Default timeout for provider requests'),
('framework.enable_caching', 'true', 'framework', 'Enable response caching'),
('framework.cache_ttl_seconds', '3600', 'framework', 'Cache time-to-live in seconds'),
('bias_detection.enabled', 'true', 'bias_detection', 'Enable bias detection'),
('bias_detection.threshold', '0.30', 'bias_detection', 'Bias score threshold for flagging'),
('learning.adaptation_rate', '0.10', 'learning', 'Learning rate for model adaptation'),
('learning.min_confidence_threshold', '0.70', 'learning', 'Minimum confidence for pattern usage'),
('telemetry.batch_size', '1000', 'framework', 'Telemetry batch processing size'),
('telemetry.flush_interval_ms', '5000', 'framework', 'Telemetry flush interval');

-- ============================================================================
-- SCHEMA VALIDATION AND COMMENTS
-- ============================================================================

COMMENT ON SCHEMA adaptive_mind IS 'Adaptive Mind Framework - Production Database Schema';
COMMENT ON TABLE providers IS 'AI service providers (OpenAI, Anthropic, etc.)';
COMMENT ON TABLE models IS 'Specific models within each provider';
COMMENT ON TABLE sessions IS 'User interaction sessions with aggregated metrics';
COMMENT ON TABLE queries IS 'Individual queries with complexity analysis';
COMMENT ON TABLE attempts IS 'Provider attempts with full performance and bias metrics';
COMMENT ON TABLE provider_performance IS 'Daily aggregated performance metrics per model';
COMMENT ON TABLE learning_patterns IS 'Machine learning patterns discovered by the system';
COMMENT ON TABLE telemetry_events IS 'Real-time system events for monitoring';
COMMENT ON TABLE system_metrics IS 'System-wide performance and health metrics';
COMMENT ON TABLE configuration IS 'Framework configuration parameters';
COMMENT ON TABLE response_cache IS 'Cached responses for performance optimization';


-- Updated Database Schema for Session 8
-- Add this to your existing PostgreSQL database

-- Session 8: Demo provider performance records table
CREATE TABLE IF NOT EXISTS demo_provider_performance_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    success BOOLEAN NOT NULL,
    response_time_ms FLOAT NOT NULL CHECK (response_time_ms >= 0),
    cost FLOAT NOT NULL CHECK (cost >= 0),
    quality_score FLOAT NOT NULL CHECK (quality_score >= 0 AND quality_score <= 1),
    error_type VARCHAR(100),
    scenario VARCHAR(100) NOT NULL DEFAULT 'general',
    load_level VARCHAR(50) NOT NULL DEFAULT 'normal',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_demo_provider_perf_provider_id_timestamp
ON demo_provider_performance_records (provider_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_demo_provider_perf_timestamp
ON demo_provider_performance_records (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_demo_provider_perf_scenario
ON demo_provider_performance_records (scenario);

CREATE INDEX IF NOT EXISTS idx_demo_provider_perf_success
ON demo_provider_performance_records (success, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_demo_provider_perf_load_level
ON demo_provider_performance_records (load_level);

-- Sample data for immediate demo functionality
INSERT INTO demo_provider_performance_records
(provider_id, timestamp, success, response_time_ms, cost, quality_score, scenario, load_level)
VALUES
('openai', NOW() - INTERVAL '2 hours', true, 250.5, 0.002, 0.95, 'customer_service', 'normal'),
('anthropic', NOW() - INTERVAL '1 hour 45 minutes', true, 180.2, 0.0025, 0.97, 'fraud_detection', 'normal'),
('google_gemini', NOW() - INTERVAL '1 hour 30 minutes', true, 320.1, 0.0015, 0.92, 'content_moderation', 'high'),
('azure', NOW() - INTERVAL '1 hour 15 minutes', false, 1200.0, 0.0, 0.0, 'financial_analysis', 'normal'),
('cohere', NOW() - INTERVAL '1 hour', true, 190.8, 0.0018, 0.94, 'medical_diagnosis_assist', 'low'),
('openai', NOW() - INTERVAL '45 minutes', true, 275.3, 0.0022, 0.93, 'customer_service', 'high'),
('anthropic', NOW() - INTERVAL '30 minutes', true, 195.7, 0.0023, 0.96, 'fraud_detection', 'normal'),
('google_gemini', NOW() - INTERVAL '15 minutes', true, 298.4, 0.0016, 0.94, 'content_moderation', 'normal'),
('azure', NOW() - INTERVAL '10 minutes', true, 410.2, 0.0019, 0.91, 'financial_analysis', 'low'),
('cohere', NOW() - INTERVAL '5 minutes', true, 205.1, 0.0017, 0.95, 'medical_diagnosis_assist', 'normal');

-- Optional: Update trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_demo_provider_performance_records_updated_at
BEFORE UPDATE ON demo_provider_performance_records
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();