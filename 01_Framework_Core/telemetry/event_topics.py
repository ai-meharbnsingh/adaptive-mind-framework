# 01_Framework_Core/telemetry/event_topics.py

"""
Defines standardized event topics for the Adaptive Mind Framework's telemetry system.
These constants ensure consistent categorization of events across different modules.
"""

# ==============================================================================
# API Call Lifecycle & Failover Events
# ==============================================================================
API_REQUEST_START = "api.request.start"
API_REQUEST_END = "api.request.end"
API_CALL_ATTEMPT = "api.call.attempt"
API_CALL_SUCCESS = "api.call.success"
API_CALL_FAILURE = "api.call.failure"
API_SERVICE_UNAVAILABLE = "api.service.unavailable"  # All providers failed

# ==============================================================================
# Resilience Mechanism Events
# ==============================================================================
PROVIDER_FAILOVER = "provider.failover"
MODEL_FAILOVER = "model.failover"
API_KEY_ROTATION = "api_key.rotation"
CIRCUIT_TRIPPED = "circuit.tripped"
CIRCUIT_RESET = "circuit.reset"
PROMPT_HUMANIZATION_ATTEMPT = "prompt.humanization.attempt"
PROMPT_HUMANIZATION_SUCCESS = "prompt.humanization.success"
PROMPT_HUMANIZATION_FAILURE = "prompt.humanization.failure"
ALL_PROVIDERS_FAILED = "all_providers.failed"
MODEL_SKIPPED_DUE_TO_COST = "model.skipped.cost_cap"


# ==============================================================================
# Learning Engine & Bias Ledger Events
# ==============================================================================
LEARNING_FEEDBACK_PUBLISHED = "learning.feedback.published"
BIAS_LOG_ENTRY_CREATED = "bias.log_entry.created"
BIAS_DETECTED = "bias.detected"
LEARNING_MODEL_UPDATE = (
    "learning_model.update"  # When an internal learning model is updated
)

# ==============================================================================
# Resource & System Health Events
# ==============================================================================
RESOURCE_PENALIZED = "resource.penalized"
RESOURCE_HEALTH_RESTORED = "resource.health.restored"
SYSTEM_HEALTH_SNAPSHOT = (
    "system.health.snapshot"  # Periodic snapshot of system health
)
API_UNHANDLED_ERROR = (
    "api.unhandled.error"  # For unexpected exceptions at the API boundary
)

# ==============================================================================
# Session 8 Demo Specific Events (for demo_backend metrics logging)
# ==============================================================================
# Used by RealTimeMetricsCollector for demo executions
DEMO_METRIC_RECORDED = "demo.metric.recorded"
DEMO_PROVIDER_STATUS_CHANGE = (
    "demo.provider.status_change"  # For the demo's ranking system
)
DEMO_RANKING_UPDATED = "demo.ranking.updated"  # For the demo's ranking system

# ==============================================================================
# Other General Event Topics
# ==============================================================================
CONFIGURATION_LOADED = "config.loaded"
ENVIRONMENT_CHECK = "env.check"
