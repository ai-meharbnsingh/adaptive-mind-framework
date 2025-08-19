-- ============================================================================
-- ADAPTIVE MIND - Initial Schema Migration (001)
-- Session 6: Database Layer Implementation
-- Migration: 001_initial_schema.sql
-- Description: Create initial database schema for Adaptive Mind Framework
-- ============================================================================

-- Migration metadata
INSERT INTO public.schema_migrations (version, description, applied_at)
VALUES ('001', 'Initial Adaptive Mind schema creation', NOW())
ON CONFLICT (version) DO NOTHING;

-- Begin transaction for atomic migration
BEGIN;

-- ============================================================================
-- EXTENSIONS AND PREREQUISITES
-- ============================================================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create migration tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    version VARCHAR(20) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rollback_sql TEXT
);

-- ============================================================================
-- SCHEMA CREATION
-- ============================================================================

-- Create dedicated schema for Adaptive Mind
CREATE SCHEMA IF NOT EXISTS adaptive_mind;

-- Set search path for this migration
SET search_path TO adaptive_mind, public;

-- ============================================================================
-- CORE INFRASTRUCTURE TABLES
-- ============================================================================

-- Providers table: Track all AI service providers
CREATE TABLE IF NOT EXISTS providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    provider_type VARCHAR(50) NOT NULL CHECK (provider_type IN ('openai', 'anthropic', 'azure', 'gemini', 'cohere', 'huggingface')),
    base_url TEXT,
    api_version VARCHAR(20),
    rate_limit_rpm INTEGER DEFAULT 60 CHECK (rate_limit_rpm > 0),
    rate_limit_tpm INTEGER DEFAULT 40000 CHECK (rate_limit_tpm > 0),
    cost_per_1k_tokens DECIMAL(10,6) CHECK (cost_per_1k_tokens >= 0),
    max_context_length INTEGER DEFAULT 4096 CHECK (max_context_length > 0),
    supports_streaming BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Models table: Track specific models within providers
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    model_identifier VARCHAR(200) NOT NULL, -- API model string
    max_tokens INTEGER DEFAULT 4096 CHECK (max_tokens > 0),
    supports_functions BOOLEAN DEFAULT false,
    supports_vision BOOLEAN DEFAULT false,
    cost_input_per_1k DECIMAL(10,6) CHECK (cost_input_per_1k >= 0),
    cost_output_per_1k DECIMAL(10,6) CHECK (cost_output_per_1k >= 0),
    is_active BOOLEAN DEFAULT true,
    capabilities JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider_id, model_identifier)
);

-- ============================================================================
-- BIAS LEDGER AND AUDIT TABLES
-- ============================================================================

-- Sessions table: Track interaction sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_type VARCHAR(50) NOT NULL CHECK (session_type IN ('query', 'conversation', 'batch', 'evaluation')),
    user_identifier VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    total_requests INTEGER DEFAULT 0 CHECK (total_requests >= 0),
    total_tokens_used INTEGER DEFAULT 0 CHECK (total_tokens_used >= 0),
    total_cost DECIMAL(10,4) DEFAULT 0.00 CHECK (total_cost >= 0),
    success_rate DECIMAL(5,4) DEFAULT 1.0000 CHECK (success_rate >= 0 AND success_rate <= 1),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Queries table: Individual query attempts
CREATE TABLE IF NOT EXISTS queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    query_hash VARCHAR(64) NOT NULL, -- SHA-256 hash for deduplication
    original_query TEXT NOT NULL,
    processed_query TEXT,
    query_category VARCHAR(100),
    complexity_score DECIMAL(3,2) DEFAULT 0.00 CHECK (complexity_score >= 0 AND complexity_score <= 1),
    tokens_in_query INTEGER DEFAULT 0 CHECK (tokens_in_query >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Attempts table: Individual provider attempts with comprehensive metrics
CREATE TABLE IF NOT EXISTS attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id UUID NOT NULL REFERENCES queries(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES models(id),
    attempt_number INTEGER NOT NULL DEFAULT 1 CHECK (attempt_number > 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failure', 'timeout', 'rate_limited', 'error')),
    response_text TEXT,
    response_metadata JSONB DEFAULT '{}',

    -- Performance metrics
    latency_ms INTEGER CHECK (latency_ms >= 0),
    tokens_input INTEGER DEFAULT 0 CHECK (tokens_input >= 0),
    tokens_output INTEGER DEFAULT 0 CHECK (tokens_output >= 0),
    cost_usd DECIMAL(8,6) DEFAULT 0.000000 CHECK (cost_usd >= 0),

    -- Quality metrics
    quality_score DECIMAL(3,2) CHECK (quality_score >= 0 AND quality_score <= 1),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    relevance_score DECIMAL(3,2) CHECK (relevance_score >= 0 AND relevance_score <= 1),
    completeness_score DECIMAL(3,2) CHECK (completeness_score >= 0 AND completeness_score <= 1),

    -- Error handling
    error_type VARCHAR(100),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),

    -- Bias detection
    bias_indicators JSONB DEFAULT '{}',
    bias_score DECIMAL(3,2) DEFAULT 0.00 CHECK (bias_score >= 0 AND bias_score <= 1),

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- LEARNING ENGINE TABLES
-- ============================================================================

-- Provider Performance table: Aggregated performance metrics
CREATE TABLE IF NOT EXISTS provider_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id),
    metric_date DATE NOT NULL,

    -- Volume metrics
    total_requests INTEGER DEFAULT 0 CHECK (total_requests >= 0),
    successful_requests INTEGER DEFAULT 0 CHECK (successful_requests >= 0),
    failed_requests INTEGER DEFAULT 0 CHECK (failed_requests >= 0),

    -- Performance metrics
    avg_latency_ms DECIMAL(8,2) CHECK (avg_latency_ms >= 0),
    p95_latency_ms DECIMAL(8,2) CHECK (p95_latency_ms >= 0),
    avg_tokens_per_request DECIMAL(8,2) CHECK (avg_tokens_per_request >= 0),

    -- Quality metrics
    avg_quality_score DECIMAL(3,2) CHECK (avg_quality_score >= 0 AND avg_quality_score <= 1),
    avg_bias_score DECIMAL(3,2) CHECK (avg_bias_score >= 0 AND avg_bias_score <= 1),
    user_satisfaction_score DECIMAL(3,2) CHECK (user_satisfaction_score >= 0 AND user_satisfaction_score <= 1),

    -- Cost metrics
    total_cost_usd DECIMAL(10,4) CHECK (total_cost_usd >= 0),
    cost_per_request DECIMAL(8,6) CHECK (cost_per_request >= 0),
    cost_efficiency_score DECIMAL(3,2) CHECK (cost_efficiency_score >= 0 AND cost_efficiency_score <= 1),

    -- Rankings
    quality_rank INTEGER CHECK (quality_rank > 0),
    speed_rank INTEGER CHECK (speed_rank > 0),
    cost_rank INTEGER CHECK (cost_rank > 0),
    overall_rank INTEGER CHECK (overall_rank > 0),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(model_id, metric_date),
    CHECK (successful_requests + failed_requests = total_requests)
);

-- Learning patterns: Track what the system learns
CREATE TABLE IF NOT EXISTS learning_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type VARCHAR(100) NOT NULL CHECK (pattern_type IN ('query_optimization', 'provider_selection', 'bias_detection', 'cost_optimization')),
    pattern_data JSONB NOT NULL,
    confidence_level DECIMAL(3,2) DEFAULT 0.00 CHECK (confidence_level >= 0 AND confidence_level <= 1),
    usage_count INTEGER DEFAULT 0 CHECK (usage_count >= 0),
    success_rate DECIMAL(5,4) DEFAULT 0.0000 CHECK (success_rate >= 0 AND success_rate <= 1),
    learned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- ============================================================================
-- TELEMETRY AND MONITORING TABLES
-- ============================================================================

-- Telemetry Events: Real-time system events
CREATE TABLE IF NOT EXISTS telemetry_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    event_topic VARCHAR(100) NOT NULL,
    source_component VARCHAR(100) NOT NULL,

    -- Event data
    event_data JSONB NOT NULL DEFAULT '{}',
    correlation_id UUID,
    parent_event_id UUID REFERENCES telemetry_events(id),

    -- Metrics
    duration_ms INTEGER CHECK (duration_ms >= 0),
    memory_usage_mb DECIMAL(8,2) CHECK (memory_usage_mb >= 0),
    cpu_usage_percent DECIMAL(5,2) CHECK (cpu_usage_percent >= 0 AND cpu_usage_percent <= 100),

    -- Context
    session_id UUID REFERENCES sessions(id),
    query_id UUID REFERENCES queries(id),
    attempt_id UUID REFERENCES attempts(id),

    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System Metrics: Aggregated system performance
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Framework performance
    framework_overhead_ms DECIMAL(6,3) DEFAULT 0.000 CHECK (framework_overhead_ms >= 0),
    active_sessions INTEGER DEFAULT 0 CHECK (active_sessions >= 0),
    queries_per_minute INTEGER DEFAULT 0 CHECK (queries_per_minute >= 0),

    -- Resource usage
    memory_usage_mb DECIMAL(8,2) CHECK (memory_usage_mb >= 0),
    cpu_usage_percent DECIMAL(5,2) CHECK (cpu_usage_percent >= 0 AND cpu_usage_percent <= 100),
    disk_usage_mb DECIMAL(10,2) CHECK (disk_usage_mb >= 0),

    -- Provider health
    healthy_providers INTEGER DEFAULT 0 CHECK (healthy_providers >= 0),
    degraded_providers INTEGER DEFAULT 0 CHECK (degraded_providers >= 0),
    failed_providers INTEGER DEFAULT 0 CHECK (failed_providers >= 0),

    -- Quality metrics
    overall_quality_score DECIMAL(3,2) CHECK (overall_quality_score >= 0 AND overall_quality_score <= 1),
    bias_detection_rate DECIMAL(5,4) CHECK (bias_detection_rate >= 0 AND bias_detection_rate <= 1),
    user_satisfaction DECIMAL(3,2) CHECK (user_satisfaction >= 0 AND user_satisfaction <= 1),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- CONFIGURATION AND CACHE TABLES
-- ============================================================================

-- Configuration table: System settings
CREATE TABLE IF NOT EXISTS configuration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(200) NOT NULL UNIQUE,
    config_value JSONB NOT NULL,
    config_type VARCHAR(50) NOT NULL CHECK (config_type IN ('framework', 'provider', 'bias_detection', 'learning', 'telemetry')),
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Response Cache: Cached responses and computations
CREATE TABLE IF NOT EXISTS response_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 hash
    query_signature VARCHAR(64) NOT NULL,
    cached_response JSONB NOT NULL,
    model_id UUID REFERENCES models(id),

    -- Cache metadata
    hit_count INTEGER DEFAULT 0 CHECK (hit_count >= 0),
    quality_score DECIMAL(3,2) CHECK (quality_score >= 0 AND quality_score <= 1),
    cache_size_bytes INTEGER CHECK (cache_size_bytes > 0),

    -- Expiration
    expires_at TIMESTAMP WITH TIME ZONE,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Primary performance indexes
CREATE INDEX IF NOT EXISTS idx_queries_hash ON queries(query_hash);
CREATE INDEX IF NOT EXISTS idx_queries_session_time ON queries(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_attempts_query_number ON attempts(query_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_attempts_model_time ON attempts(model_id, created_at);
CREATE INDEX IF NOT EXISTS idx_attempts_status_time ON attempts(status, created_at);

-- Performance optimization indexes
CREATE INDEX IF NOT EXISTS idx_attempts_performance ON attempts(model_id, status, created_at) WHERE status = 'success';
CREATE INDEX IF NOT EXISTS idx_attempts_bias_detection ON attempts(bias_score, created_at) WHERE bias_score > 0.00;
CREATE INDEX IF NOT EXISTS idx_queries_complexity ON queries(complexity_score DESC, created_at);

-- Telemetry indexes
CREATE INDEX IF NOT EXISTS idx_telemetry_type_time ON telemetry_events(event_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_correlation ON telemetry_events(correlation_id, timestamp) WHERE correlation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_telemetry_session_time ON telemetry_events(session_id, timestamp) WHERE session_id IS NOT NULL;

-- Provider performance indexes
CREATE INDEX IF NOT EXISTS idx_provider_performance_ranking ON provider_performance(metric_date, overall_rank);
CREATE INDEX IF NOT EXISTS idx_provider_performance_model_date ON provider_performance(model_id, metric_date);

-- System metrics indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(metric_timestamp);

-- Learning patterns indexes
CREATE INDEX IF NOT EXISTS idx_learning_patterns_type_confidence ON learning_patterns(pattern_type, confidence_level DESC) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_learning_patterns_usage ON learning_patterns(usage_count DESC, last_used_at) WHERE is_active = true;

-- Configuration indexes
CREATE INDEX IF NOT EXISTS idx_configuration_type_active ON configuration(config_type, is_active) WHERE is_active = true;

-- Cache indexes
CREATE INDEX IF NOT EXISTS idx_response_cache_query_sig ON response_cache(query_signature);
CREATE INDEX IF NOT EXISTS idx_response_cache_expires ON response_cache(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_response_cache_last_accessed ON response_cache(last_accessed_at);

-- Partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_providers_active ON providers(name, provider_type) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_models_active ON models(provider_id, name) WHERE is_active = true;

-- ============================================================================
-- JSONB GIN INDEXES FOR FAST JSON QUERIES
-- ============================================================================

-- JSONB indexes for efficient JSON queries
CREATE INDEX IF NOT EXISTS idx_attempts_response_metadata_gin ON attempts USING GIN(response_metadata);
CREATE INDEX IF NOT EXISTS idx_attempts_bias_indicators_gin ON attempts USING GIN(bias_indicators);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_data_gin ON telemetry_events USING GIN(event_data);
CREATE INDEX IF NOT EXISTS idx_learning_patterns_data_gin ON learning_patterns USING GIN(pattern_data);
CREATE INDEX IF NOT EXISTS idx_providers_metadata_gin ON providers USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_models_capabilities_gin ON models USING GIN(capabilities);

-- ============================================================================
-- TRIGGERS AND FUNCTIONS
-- ============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ language 'plpgsql';

-- Apply update triggers to tables with updated_at columns
CREATE TRIGGER update_providers_updated_at
    BEFORE UPDATE ON providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_models_updated_at
    BEFORE UPDATE ON models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_configuration_updated_at
    BEFORE UPDATE ON configuration
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_provider_performance_updated_at
    BEFORE UPDATE ON provider_performance
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update session statistics when attempts are inserted
CREATE OR REPLACE FUNCTION update_session_stats()
RETURNS TRIGGER AS $
DECLARE
    session_uuid UUID;
BEGIN
    -- Get session_id from the query
    SELECT session_id INTO session_uuid
    FROM queries
    WHERE id = NEW.query_id;

    IF session_uuid IS NOT NULL THEN
        UPDATE sessions
        SET total_requests = total_requests + 1,
            total_tokens_used = total_tokens_used + COALESCE(NEW.tokens_input, 0) + COALESCE(NEW.tokens_output, 0),
            total_cost = total_cost + COALESCE(NEW.cost_usd, 0)
        WHERE id = session_uuid;

        -- Update success rate if attempt completed
        IF NEW.status IN ('success', 'failure') THEN
            UPDATE sessions
            SET success_rate = (
                SELECT COALESCE(
                    CAST(COUNT(*) FILTER (WHERE a.status = 'success') AS DECIMAL) /
                    NULLIF(COUNT(*), 0),
                    0
                )
                FROM attempts a
                JOIN queries q ON a.query_id = q.id
                WHERE q.session_id = session_uuid
                    AND a.status IN ('success', 'failure')
            )
            WHERE id = session_uuid;
        END IF;
    END IF;

    RETURN NEW;
END;
$ language 'plpgsql';

-- Trigger to update session stats when attempts are inserted
CREATE TRIGGER update_session_stats_trigger
    AFTER INSERT ON attempts
    FOR EACH ROW EXECUTE FUNCTION update_session_stats();

-- Function to automatically end sessions when they become inactive
CREATE OR REPLACE FUNCTION auto_end_inactive_sessions()
RETURNS void AS $
BEGIN
    UPDATE sessions
    SET ended_at = NOW()
    WHERE ended_at IS NULL
        AND started_at < NOW() - INTERVAL '1 hour'
        AND NOT EXISTS (
            SELECT 1 FROM queries q
            JOIN attempts a ON q.id = a.query_id
            WHERE q.session_id = sessions.id
                AND a.created_at > NOW() - INTERVAL '10 minutes'
        );
END;
$ language 'plpgsql';

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Provider performance dashboard view
CREATE OR REPLACE VIEW provider_dashboard AS
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
CREATE OR REPLACE VIEW system_health AS
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
CREATE OR REPLACE VIEW bias_detection_summary AS
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

-- Active sessions view
CREATE OR REPLACE VIEW active_sessions AS
SELECT
    s.id,
    s.session_type,
    s.user_identifier,
    s.started_at,
    s.total_requests,
    s.total_tokens_used,
    s.total_cost,
    s.success_rate,
    COUNT(q.id) as query_count,
    MAX(a.created_at) as last_activity
FROM sessions s
LEFT JOIN queries q ON s.id = q.session_id
LEFT JOIN attempts a ON q.id = a.query_id
WHERE s.ended_at IS NULL
GROUP BY s.id, s.session_type, s.user_identifier, s.started_at,
         s.total_requests, s.total_tokens_used, s.total_cost, s.success_rate
ORDER BY s.started_at DESC;

-- ============================================================================
-- INITIAL CONFIGURATION DATA
-- ============================================================================

-- Insert default framework configuration
INSERT INTO configuration (config_key, config_value, config_type, description) VALUES
('framework.max_concurrent_requests', '100', 'framework', 'Maximum concurrent requests to handle'),
('framework.default_timeout_ms', '30000', 'framework', 'Default timeout for provider requests'),
('framework.enable_caching', 'true', 'framework', 'Enable response caching'),
('framework.cache_ttl_seconds', '3600', 'framework', 'Cache time-to-live in seconds'),
('framework.enable_retry', 'true', 'framework', 'Enable automatic retry on failures'),
('framework.max_retry_attempts', '3', 'framework', 'Maximum retry attempts per request'),

-- Bias detection configuration
('bias_detection.enabled', 'true', 'bias_detection', 'Enable bias detection'),
('bias_detection.threshold', '0.30', 'bias_detection', 'Bias score threshold for flagging'),
('bias_detection.auto_remediation', 'true', 'bias_detection', 'Enable automatic bias remediation'),
('bias_detection.sensitivity', 'medium', 'bias_detection', 'Bias detection sensitivity level'),

-- Learning engine configuration
('learning.adaptation_rate', '0.10', 'learning', 'Learning rate for model adaptation'),
('learning.min_confidence_threshold', '0.70', 'learning', 'Minimum confidence for pattern usage'),
('learning.enable_auto_optimization', 'true', 'learning', 'Enable automatic provider optimization'),
('learning.feedback_integration', 'true', 'learning', 'Enable user feedback integration'),

-- Telemetry configuration
('telemetry.batch_size', '1000', 'telemetry', 'Telemetry batch processing size'),
('telemetry.flush_interval_ms', '5000', 'telemetry', 'Telemetry flush interval'),
('telemetry.enable_detailed_logging', 'true', 'telemetry', 'Enable detailed telemetry logging'),
('telemetry.retention_days', '365', 'telemetry', 'Telemetry data retention period'),

-- Provider defaults
('provider.openai.rate_limit_rpm', '3500', 'provider', 'OpenAI requests per minute limit'),
('provider.anthropic.rate_limit_rpm', '5000', 'provider', 'Anthropic requests per minute limit'),
('provider.azure.rate_limit_rpm', '10000', 'provider', 'Azure OpenAI requests per minute limit'),
('provider.gemini.rate_limit_rpm', '2000', 'provider', 'Google Gemini requests per minute limit')

ON CONFLICT (config_key) DO NOTHING;

-- Insert default providers (inactive by default for security)
INSERT INTO providers (name, provider_type, base_url, is_active) VALUES
('OpenAI', 'openai', 'https://api.openai.com/v1', false),
('Anthropic', 'anthropic', 'https://api.anthropic.com', false),
('Azure OpenAI', 'azure', NULL, false),
('Google Gemini', 'gemini', 'https://generativelanguage.googleapis.com', false)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- SECURITY AND PERMISSIONS
-- ============================================================================

-- Create application role if it doesn't exist
DO $
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'adaptive_mind_app') THEN
        CREATE ROLE adaptive_mind_app WITH LOGIN;
    END IF;
END
$;

-- Grant permissions to application role
GRANT USAGE ON SCHEMA adaptive_mind TO adaptive_mind_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA adaptive_mind TO adaptive_mind_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA adaptive_mind TO adaptive_mind_app;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION update_updated_at_column() TO adaptive_mind_app;
GRANT EXECUTE ON FUNCTION update_session_stats() TO adaptive_mind_app;
GRANT EXECUTE ON FUNCTION auto_end_inactive_sessions() TO adaptive_mind_app;

-- Create read-only role for analytics
DO $
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'adaptive_mind_readonly') THEN
        CREATE ROLE adaptive_mind_readonly WITH LOGIN;
    END IF;
END
$;

GRANT USAGE ON SCHEMA adaptive_mind TO adaptive_mind_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA adaptive_mind TO adaptive_mind_readonly;

-- ============================================================================
-- TABLE COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON SCHEMA adaptive_mind IS 'Adaptive Mind Framework - Production Database Schema';
COMMENT ON TABLE providers IS 'AI service providers (OpenAI, Anthropic, Azure, Gemini, etc.)';
COMMENT ON TABLE models IS 'Specific AI models within each provider';
COMMENT ON TABLE sessions IS 'User interaction sessions with aggregated metrics';
COMMENT ON TABLE queries IS 'Individual queries with complexity analysis and deduplication';
COMMENT ON TABLE attempts IS 'Provider attempts with comprehensive performance and bias metrics';
COMMENT ON TABLE provider_performance IS 'Daily aggregated performance metrics per model';
COMMENT ON TABLE learning_patterns IS 'Machine learning patterns discovered by the system';
COMMENT ON TABLE telemetry_events IS 'Real-time system events for monitoring and debugging';
COMMENT ON TABLE system_metrics IS 'System-wide performance and health metrics';
COMMENT ON TABLE configuration IS 'Framework configuration parameters and settings';
COMMENT ON TABLE response_cache IS 'Cached responses for performance optimization';

-- ============================================================================
-- VALIDATION AND CLEANUP
-- ============================================================================

-- Validate that all required tables exist
DO $
DECLARE
    required_tables TEXT[] := ARRAY[
        'providers', 'models', 'sessions', 'queries', 'attempts',
        'provider_performance', 'learning_patterns', 'telemetry_events',
        'system_metrics', 'configuration', 'response_cache'
    ];
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY required_tables
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'adaptive_mind'
            AND table_name = table_name
        ) THEN
            RAISE EXCEPTION 'Required table % was not created successfully', table_name;
        END IF;
    END LOOP;

    RAISE NOTICE 'All required tables created successfully';
END
$;

-- Update migration record with completion timestamp
UPDATE public.schema_migrations
SET applied_at = NOW()
WHERE version = '001';

-- Commit the migration
COMMIT;

-- ============================================================================
-- POST-MIGRATION TASKS
-- ============================================================================

-- Analyze tables for optimal query planning
ANALYZE adaptive_mind.providers;
ANALYZE adaptive_mind.models;
ANALYZE adaptive_mind.sessions;
ANALYZE adaptive_mind.queries;
ANALYZE adaptive_mind.attempts;
ANALYZE adaptive_mind.provider_performance;
ANALYZE adaptive_mind.learning_patterns;
ANALYZE adaptive_mind.telemetry_events;
ANALYZE adaptive_mind.system_metrics;
ANALYZE adaptive_mind.configuration;
ANALYZE adaptive_mind.response_cache;

-- Log migration completion
INSERT INTO adaptive_mind.telemetry_events (
    event_type,
    event_topic,
    source_component,
    event_data
) VALUES (
    'migration',
    'schema.migration_completed',
    'database_migration',
    '{"version": "001", "description": "Initial schema creation", "tables_created": 11, "indexes_created": 25, "views_created": 4}'
);

-- Success message
SELECT 'Adaptive Mind database schema migration 001 completed successfully!' as migration_status;