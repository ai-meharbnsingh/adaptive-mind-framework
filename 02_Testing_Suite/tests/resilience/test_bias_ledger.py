# tests/resilience/test_bias_ledger.py

from datetime import datetime, timezone  # Added for ProviderProfiles mock
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from antifragile_framework.config.schemas import CostProfile, ProviderProfiles
from antifragile_framework.core.schemas import RequestContext
from antifragile_framework.providers.api_abstraction_layer import (
    ChatMessage,
    CompletionResponse,
    TokenUsage,
)
from antifragile_framework.resilience.bias_ledger import BiasLedger
from telemetry import event_topics
from telemetry.core_logger import UniversalEventSchema
from telemetry.event_bus import EventBus


@pytest.fixture
def mock_event_bus():
    bus = Mock(spec=EventBus)
    bus.publish = Mock()
    return bus


@pytest.fixture
def mock_logger():
    with patch(
        "antifragile_framework.resilience.bias_ledger.core_logger"
    ) as mock_logger_instance:
        yield mock_logger_instance


@pytest.fixture
def mock_provider_profiles():
    """Provides a mock ProviderProfiles object for testing cost calculations."""
    # Ensure schema_version and last_updated_utc are present as per config.schemas.py
    return ProviderProfiles(
        schema_version="1.0",
        last_updated_utc=datetime.now(timezone.utc).isoformat(),
        profiles={
            "openai": {
                "_default": CostProfile(
                    input_cpm=Decimal("0.50"), output_cpm=Decimal("1.50")
                ),
                "gpt-4o": CostProfile(
                    input_cpm=Decimal("5.00"), output_cpm=Decimal("15.00")
                ),
            },
            "anthropic": {
                # No default, to test missing profile case
                "claude-3-opus-20240229": CostProfile(
                    input_cpm=Decimal("15.00"), output_cpm=Decimal("75.00")
                )
            },
        },
    )


@pytest.fixture
def basic_context():
    messages = [ChatMessage(role="user", content="Original prompt")]
    return RequestContext(
        initial_messages=messages,
        final_messages=messages,
        request_id="test-uuid-123",
    )


def test_bias_ledger_initialization(mock_event_bus, mock_provider_profiles):
    ledger = BiasLedger(
        event_bus=mock_event_bus, provider_profiles=mock_provider_profiles
    )
    assert ledger.event_bus is mock_event_bus
    assert ledger.provider_profiles is mock_provider_profiles
    assert ledger.prompt_preview_len == 512


def test_log_successful_request(mock_event_bus, mock_logger, basic_context):
    ledger = BiasLedger(event_bus=mock_event_bus)
    response = CompletionResponse(
        success=True,
        content="Successful response",
        model_used="gpt-4o",
        latency_ms=100.0,
        metadata={"provider_name": "openai"},
    )
    basic_context.api_call_count = 1

    entry = ledger.log_request_lifecycle(
        context=basic_context,
        initial_selection_mode="VALUE_DRIVEN",  # NEW: Added argument
        final_response=response,
        resilience_score=1.0,
    )

    mock_logger.log.assert_called_once()
    log_arg = mock_logger.log.call_args[0][0]
    assert isinstance(log_arg, UniversalEventSchema)
    assert log_arg.event_type == event_topics.BIAS_LOG_ENTRY_CREATED

    payload = log_arg.payload
    assert entry.outcome == "SUCCESS"
    assert payload["outcome"] == "SUCCESS"
    assert payload["request_id"] == "test-uuid-123"
    assert payload["initial_prompt_preview"] == "Original prompt"
    assert payload["final_response_preview"] == "Successful response"
    assert payload["final_prompt_preview"] is None
    assert payload["mitigation_attempted"] is False
    assert payload["final_provider"] == "openai"
    assert payload["final_model"] == "gpt-4o"
    assert (
        payload["initial_selection_mode"] == "VALUE_DRIVEN"
    )  # NEW: Assert the new field


def test_log_mitigated_success_request(mock_event_bus, mock_logger, basic_context):
    ledger = BiasLedger(event_bus=mock_event_bus)
    basic_context.mitigation_attempted = True
    basic_context.final_messages = [
        ChatMessage(role="user", content="Rephrased prompt")
    ]
    response = CompletionResponse(
        success=True,
        content="Successful response",
        model_used="gpt-4o",
        latency_ms=100.0,
    )

    entry = ledger.log_request_lifecycle(
        context=basic_context,
        initial_selection_mode="VALUE_DRIVEN",  # NEW: Added argument
        final_response=response,
    )

    payload = mock_logger.log.call_args[0][0].payload
    assert entry.outcome == "MITIGATED_SUCCESS"
    assert payload["outcome"] == "MITIGATED_SUCCESS"
    assert payload["final_prompt_preview"] == "Rephrased prompt"
    assert payload["mitigation_attempted"] is True
    assert payload["mitigation_succeeded"] is True
    assert (
        payload["initial_selection_mode"] == "VALUE_DRIVEN"
    )  # NEW: Assert the new field


def test_log_failed_request(mock_event_bus, mock_logger, basic_context):
    ledger = BiasLedger(event_bus=mock_event_bus)
    error = Exception("Something went wrong")

    entry = ledger.log_request_lifecycle(
        context=basic_context,
        initial_selection_mode="VALUE_DRIVEN",  # NEW: Added argument
        final_error=error,
    )

    payload = mock_logger.log.call_args[0][0].payload
    assert entry.outcome == "FAILURE"
    assert payload["outcome"] == "FAILURE"
    assert payload["final_response_preview"] is None
    assert payload["final_provider"] is None
    assert payload["final_model"] is None
    assert (
        payload["initial_selection_mode"] == "VALUE_DRIVEN"
    )  # NEW: Assert the new field


# --- NEW: Tests for Cost Calculation ---


def test_cost_calculation_with_specific_profile(
    mock_event_bus, mock_logger, basic_context, mock_provider_profiles
):
    """Verify correct cost calculation using a specific model's profile."""
    ledger = BiasLedger(
        event_bus=mock_event_bus, provider_profiles=mock_provider_profiles
    )
    response = CompletionResponse(
        success=True,
        content="Response",
        model_used="gpt-4o",
        latency_ms=100.0,
        metadata={"provider_name": "openai"},
        usage=TokenUsage(input_tokens=1000, output_tokens=2000),
    )

    entry = ledger.log_request_lifecycle(
        context=basic_context,
        initial_selection_mode="VALUE_DRIVEN",  # NEW: Added argument
        final_response=response,
    )

    # Expected cost: (1000 * 5.00 / 1M) + (2000 * 15.00 / 1M) = 0.005 + 0.03 = 0.035
    expected_cost = Decimal("0.035000")

    assert entry.input_tokens == 1000
    assert entry.output_tokens == 2000
    assert entry.estimated_cost_usd == expected_cost


def test_cost_calculation_uses_default_profile(
    mock_event_bus, mock_logger, basic_context, mock_provider_profiles
):
    """Verify fallback to the provider's default profile when a specific model profile is missing."""
    ledger = BiasLedger(
        event_bus=mock_event_bus, provider_profiles=mock_provider_profiles
    )
    response = CompletionResponse(
        success=True,
        content="Response",
        model_used="gpt-4-turbo",  # This model is not in our mock profile
        latency_ms=120.0,
        metadata={"provider_name": "openai"},
        usage=TokenUsage(input_tokens=10000, output_tokens=5000),
    )

    entry = ledger.log_request_lifecycle(
        context=basic_context,
        initial_selection_mode="VALUE_DRIVEN",  # NEW: Added argument
        final_response=response,
    )

    # Expected cost: (10000 * 0.50 / 1M) + (5000 * 1.50 / 1M) = 0.005 + 0.0075 = 0.0125
    expected_cost = Decimal("0.012500")

    assert entry.estimated_cost_usd == expected_cost


def test_cost_calculation_handles_missing_provider_profile(
    mock_event_bus, mock_logger, basic_context, mock_provider_profiles
):
    """Verify cost is None when the provider has no profile and no default."""
    ledger = BiasLedger(
        event_bus=mock_event_bus, provider_profiles=mock_provider_profiles
    )
    response = CompletionResponse(
        success=True,
        content="Response",
        model_used="claude-3-sonnet",  # Not in profile
        latency_ms=130.0,
        metadata={"provider_name": "anthropic"},
        usage=TokenUsage(input_tokens=1000, output_tokens=2000),
    )

    entry = ledger.log_request_lifecycle(
        context=basic_context,
        initial_selection_mode="VALUE_DRIVEN",  # NEW: Added argument
        final_response=response,
    )

    assert entry.estimated_cost_usd is None
    assert entry.input_tokens == 1000
    assert entry.output_tokens == 2000


def test_no_cost_calculated_if_usage_data_is_missing(
    mock_event_bus, mock_logger, basic_context, mock_provider_profiles
):
    """Verify cost is None if the CompletionResponse has no token usage data."""
    ledger = BiasLedger(
        event_bus=mock_event_bus, provider_profiles=mock_provider_profiles
    )
    response = CompletionResponse(
        success=True,
        content="Response",
        model_used="gpt-4o",
        latency_ms=100.0,
        metadata={"provider_name": "openai"},
        usage=None,
    )

    entry = ledger.log_request_lifecycle(
        context=basic_context,
        initial_selection_mode="VALUE_DRIVEN",  # NEW: Added argument
        final_response=response,
    )

    assert entry.input_tokens is None
    assert entry.output_tokens is None
    assert entry.estimated_cost_usd is None
