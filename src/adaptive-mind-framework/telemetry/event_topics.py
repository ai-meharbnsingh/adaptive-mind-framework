# telemetry/event_topics.py

"""
Central repository for event topic constants.

Using constants for topic names helps prevent typos and makes it easy to
find all usages of a specific event across the codebase.
"""

# Failover Engine Events
API_CALL_SUCCESS = "api.call.success"
API_CALL_FAILURE = "api.call.failure"
API_KEY_ROTATION = "api.key.rotation"
MODEL_FAILOVER = "model.failover"
PROVIDER_FAILOVER = "provider.failover"
CIRCUIT_TRIPPED = "circuit.tripped"
CIRCUIT_RESET = "circuit.reset"
ALL_PROVIDERS_FAILED = "all.providers.failed"
MODEL_SKIPPED_DUE_TO_COST = "model.skipped_due_to_cost" # NEW: Added for cost cap enforcement

# Resource Guard Events
RESOURCE_PENALIZED = "resource.penalized"
RESOURCE_HEALTH_RESTORED = "resource.health.restored"
ALL_RESOURCES_HEALED = "resource.healed.all"

# Prompt Rewriter Events
PROMPT_HUMANIZATION_ATTEMPT = "prompt.humanization.attempt"
PROMPT_HUMANIZATION_SUCCESS = "prompt.humanization.success"
PROMPT_HUMANIZATION_FAILURE = "prompt.humanization.failure"

# Bias Ledger Events
BIAS_LOG_ENTRY_CREATED = "bias.ledger.entry.created"

# API Layer Events
API_REQUEST_START = "api.request.start"
API_REQUEST_END = "api.request.end"
API_UNHANDLED_ERROR = "api.error.unhandled"
API_SERVICE_UNAVAILABLE = "api.error.service_unavailable"
API_PROVIDER_SKIP = "api.provider.skip"
API_PROVIDER_FAILOVER_ATTEMPT = "api.provider.failover_attempt"

# Learning Engine Events
LEARNING_FEEDBACK_PUBLISHED = "learning.feedback.published"