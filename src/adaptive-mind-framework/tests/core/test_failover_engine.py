# tests/core/test_failover_engine.py

import pytest
import openai
import anthropic
from unittest.mock import AsyncMock, call, Mock, MagicMock
from decimal import Decimal
from datetime import datetime, timezone
from contextlib import contextmanager

from antifragile_framework.core.failover_engine import FailoverEngine
from antifragile_framework.core.exceptions import AllProvidersFailedError, ContentPolicyError, RewriteFailedError, \
    NoResourcesAvailableError
from antifragile_framework.core.circuit_breaker import CircuitBreakerState, CircuitBreakerError
# ==============================================================================
# REFACTOR: Import TokenUsage to fix the test fixture bug
# ==============================================================================
from antifragile_framework.providers.api_abstraction_layer import ChatMessage, CompletionResponse, TokenUsage
from antifragile_framework.providers.provider_registry import get_default_provider_registry
from antifragile_framework.resilience.prompt_rewriter import PromptRewriter
from antifragile_framework.utils.error_parser import ErrorCategory, ErrorDetails
from antifragile_framework.core.resource_guard import MonitoredResource, ResourceGuard
from antifragile_framework.core.provider_ranking_engine import ProviderRankingEngine
from antifragile_framework.config.schemas import ProviderProfiles, CostProfile
from telemetry import event_topics


# --- Test Fixtures ---

@pytest.fixture
def multi_provider_config():
    return {
        "openai": {
            "api_keys": ["key-openai-1", "key-openai-2"],
            "resource_config": {"penalty": 0.5, "cooldown": 300},
            "circuit_breaker_config": {"failure_threshold": 3}
        },
        "anthropic": {
            "api_keys": ["key-claude-1"],
            "resource_config": {"penalty": 0.5, "cooldown": 300},
            "circuit_breaker_config": {"failure_threshold": 2}
        },
        "google_gemini": {
            "api_keys": ["key-gemini-1"],
            "resource_config": {}, "circuit_breaker_config": {}
        }
    }


@pytest.fixture
def mock_provider_profiles():
    return ProviderProfiles(
        schema_version="1.0",
        last_updated_utc=datetime.now(timezone.utc).isoformat(),
        profiles={
            "openai": {
                "gpt-4o": CostProfile(input_cpm=Decimal("5.00"), output_cpm=Decimal("15.00")),
                "gpt-4-turbo": CostProfile(input_cpm=Decimal("10.00"), output_cpm=Decimal("30.00")),
                "_default": CostProfile(input_cpm=Decimal("7.00"), output_cpm=Decimal("21.00"))
            },
            "anthropic": {
                "claude-3-opus": CostProfile(input_cpm=Decimal("15.00"), output_cpm=Decimal("75.00")),
                "claude-3-sonnet": CostProfile(input_cpm=Decimal("3.00"), output_cpm=Decimal("15.00")),
                "claude-3-5-sonnet-20240620": CostProfile(input_cpm=Decimal("3.00"), output_cpm=Decimal("15.00")),
                "_default": CostProfile(input_cpm=Decimal("9.00"), output_cpm=Decimal("45.00"))
            },
            "google_gemini": {
                "gemini-1.5-flash-latest": CostProfile(input_cpm=Decimal("0.35"), output_cpm=Decimal("1.05")),
                "gemini-pro": CostProfile(input_cpm=Decimal("0.25"), output_cpm=Decimal("0.50")),
                "_default": CostProfile(input_cpm=Decimal("0.30"), output_cpm=Decimal("0.75"))
            }
        }
    )


@pytest.fixture
def mock_rewriter():
    rewriter = Mock(spec=PromptRewriter)
    rewriter.rephrase_for_policy_compliance = AsyncMock()
    return rewriter


@pytest.fixture
def mock_ranking_engine():
    ranking_engine = Mock(spec=ProviderRankingEngine)
    ranking_engine.get_ranked_providers = Mock(return_value=[])
    return ranking_engine


@pytest.fixture
def mock_bias_ledger(mocker):
    mock_ledger = mocker.patch('antifragile_framework.resilience.bias_ledger.BiasLedger', autospec=True).return_value
    mock_ledger.log_request_lifecycle = Mock(return_value=MagicMock())
    return mock_ledger


@pytest.fixture
def mock_guards(mocker):
    created_guards = {}

    def guard_factory(*args, **kwargs):
        provider_name = kwargs.get("provider_name", args[0] if args else "unknown")
        mock_guard = MagicMock(spec=ResourceGuard)
        api_keys = kwargs.get("api_keys", [])
        num_keys = len(api_keys)

        @contextmanager
        def _mock_resource_context(key_id):
            mock_resource = MagicMock(spec=MonitoredResource)
            mock_resource.value = key_id
            mock_resource.safe_value = f"{key_id[:4]}...{key_id[-4:]}"
            yield mock_resource

        def default_side_effect_factory():
            call_count = 0

            def side_effect():
                nonlocal call_count
                call_count += 1
                if call_count <= num_keys:
                    return _mock_resource_context(api_keys[call_count - 1])
                else:
                    raise NoResourcesAvailableError(provider=provider_name)

            return side_effect

        mock_guard.get_resource.side_effect = default_side_effect_factory()
        mock_guard.has_healthy_resources.return_value = True
        created_guards[provider_name] = mock_guard
        return mock_guard

    mocker.patch('antifragile_framework.core.failover_engine.ResourceGuard', side_effect=guard_factory)
    return created_guards


@pytest.fixture(autouse=True)
def reset_bias_ledger_mock(mock_bias_ledger):
    yield
    mock_bias_ledger.reset_mock()


@pytest.fixture
def engine(multi_provider_config, mock_ranking_engine, mock_provider_profiles, mock_bias_ledger, mock_guards):
    # ==============================================================================
    # REFACTOR: Inject the default provider registry into the engine
    # ==============================================================================
    return FailoverEngine(
        provider_configs=multi_provider_config,
        provider_registry=get_default_provider_registry(),
        provider_ranking_engine=mock_ranking_engine,
        provider_profiles=mock_provider_profiles,
        bias_ledger=mock_bias_ledger
    )


@pytest.fixture
def engine_with_rewriter(multi_provider_config, mock_rewriter, mock_ranking_engine, mock_provider_profiles,
                         mock_bias_ledger, mock_guards):
    # ==============================================================================
    # REFACTOR: Inject the default provider registry into the engine
    # ==============================================================================
    return FailoverEngine(
        provider_configs=multi_provider_config,
        provider_registry=get_default_provider_registry(),
        prompt_rewriter=mock_rewriter,
        provider_ranking_engine=mock_ranking_engine,
        provider_profiles=mock_provider_profiles,
        bias_ledger=mock_bias_ledger
    )


@pytest.fixture
def mock_openai_adapter(mocker):
    return mocker.patch(
        'antifragile_framework.providers.provider_adapters.openai_adapter.OpenAIProvider.agenerate_completion',
        new_callable=AsyncMock)


@pytest.fixture
def mock_anthropic_adapter(mocker):
    return mocker.patch(
        'antifragile_framework.providers.provider_adapters.claude_adapter.ClaudeProvider.agenerate_completion',
        new_callable=AsyncMock)


@pytest.fixture
def mock_gemini_adapter(mocker):
    return mocker.patch(
        'antifragile_framework.providers.provider_adapters.gemini_adapter.GeminiProvider.agenerate_completion',
        new_callable=AsyncMock)


# --- Standard Failover Tests (Refactored for new mock_guards fixture) ---
@pytest.mark.asyncio
async def test_success_on_first_provider_model_and_key(engine, mock_openai_adapter, mock_guards):
    mock_openai_adapter.return_value = CompletionResponse(success=True, content="Success", latency_ms=100.0)
    messages = [ChatMessage(role="user", content="Test")]
    response = await engine.execute_request(model_priority_map={'openai': ['gpt-4o']}, messages=messages)
    assert response.success is True
    mock_openai_adapter.assert_called_once_with(messages, api_key_override="key-openai-1", model='gpt-4o')
    assert mock_guards['openai'].get_resource.call_count == 1


@pytest.mark.asyncio
async def test_key_rotation_on_single_model(engine, mock_openai_adapter, mock_bias_ledger, mock_guards):
    mock_openai_adapter.side_effect = [
        openai.APIError("Fail", request=Mock(), body=None),
        CompletionResponse(success=True, content="Success", latency_ms=100.0)
    ]
    messages = [ChatMessage(role="user", content="Test")]
    response = await engine.execute_request(model_priority_map={'openai': ['gpt-4o']}, messages=messages)
    assert response.success is True
    assert mock_openai_adapter.call_count == 2
    assert mock_guards['openai'].get_resource.call_count == 2
    assert mock_bias_ledger.log_request_lifecycle.call_args.kwargs['context'].api_call_count == 2


@pytest.mark.asyncio
async def test_model_failover_when_first_model_exhausts_keys(engine, mock_openai_adapter, mock_guards):
    @contextmanager
    def _mock_resource_context(key_id):
        yield MagicMock(value=key_id)

    call_count = 0
    def side_effect_func():
        nonlocal call_count
        call_count += 1
        if call_count <= 2: return _mock_resource_context("key-openai-" + str(call_count)) # keys for model 1
        if call_count == 3: raise NoResourcesAvailableError(provider="openai")
        if call_count == 4: return _mock_resource_context("key-openai-1") # key for model 2
        raise NoResourcesAvailableError(provider="openai")

    mock_guards['openai'].get_resource.side_effect = side_effect_func

    mock_openai_adapter.side_effect = [
        openai.APIError("Fail key 1 model 1", request=Mock(), body=None),
        openai.APIError("Fail key 2 model 1", request=Mock(), body=None),
        CompletionResponse(success=True, content="Success on model 2", latency_ms=150.0)
    ]
    messages = [ChatMessage(role="user", content="Test")]
    response = await engine.execute_request(model_priority_map={'openai': ['gpt-4o', 'gpt-4-turbo']}, messages=messages)
    assert response.success is True
    assert response.content == "Success on model 2"
    assert mock_openai_adapter.call_count == 3
    calls = [
        call(messages, api_key_override="key-openai-1", model='gpt-4o'),
        call(messages, api_key_override="key-openai-2", model='gpt-4o'),
        call(messages, api_key_override="key-openai-1", model='gpt-4-turbo')
    ]
    mock_openai_adapter.assert_has_calls(calls)


@pytest.mark.asyncio
async def test_model_specific_error_skips_key_rotation_and_tries_next_model(engine, mock_openai_adapter, mock_guards):
    error = openai.NotFoundError("The model `gpt-4o` does not exist", response=Mock(), body=None)
    mock_openai_adapter.side_effect = [
        error,
        CompletionResponse(success=True, content="Success", latency_ms=100.0)
    ]
    messages = [ChatMessage(role="user", content="Test")]
    response = await engine.execute_request(model_priority_map={'openai': ['gpt-4o', 'gpt-4-turbo']}, messages=messages)
    assert response.success is True
    assert mock_openai_adapter.call_count == 2
    assert mock_guards['openai'].get_resource.call_count == 2
    calls = [
        call(messages, api_key_override="key-openai-1", model='gpt-4o'),
        call(messages, api_key_override="key-openai-1", model='gpt-4-turbo')
    ]
    mock_openai_adapter.assert_has_calls(calls)


@pytest.mark.asyncio
async def test_provider_failover_on_all_models_failing_due_to_cooldown(engine, mock_openai_adapter,
                                                                       mock_anthropic_adapter, mock_guards):
    mock_openai_adapter.side_effect = openai.APIError("Fail", request=Mock(), body=None)
    mock_anthropic_adapter.return_value = CompletionResponse(success=True, content="Success", latency_ms=100.0)
    messages = [ChatMessage(role="user", content="Test")]
    response = await engine.execute_request(model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-opus']},
                                            messages=messages)
    assert response.success is True
    assert mock_openai_adapter.call_count == 2
    assert mock_guards['openai'].get_resource.call_count == 3
    mock_anthropic_adapter.assert_called_once()
    assert mock_guards['anthropic'].get_resource.call_count == 1


@pytest.mark.asyncio
async def test_provider_failover_on_circuit_breaker_trip(engine, mock_openai_adapter, mock_anthropic_adapter,
                                                         mock_guards):
    engine.circuit_breakers.get_breaker("openai").check = Mock(side_effect=CircuitBreakerError("Circuit is OPEN"))
    mock_anthropic_adapter.return_value = CompletionResponse(success=True, content="Success", latency_ms=100.0)
    messages = [ChatMessage(role="user", content="Test")]
    response = await engine.execute_request(model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-opus']},
                                            messages=messages)
    assert response.success is True
    mock_openai_adapter.assert_not_called()
    assert mock_guards['openai'].get_resource.call_count == 0
    mock_anthropic_adapter.assert_called_once()
    assert mock_guards['anthropic'].get_resource.call_count == 1


@pytest.mark.asyncio
async def test_all_providers_and_models_fail_raises_final_error(engine, mock_openai_adapter, mock_anthropic_adapter,
                                                                mock_gemini_adapter, mock_guards):
    mock_openai_adapter.side_effect = openai.APIError("Fail", request=Mock(), body=None)
    mock_anthropic_adapter.side_effect = anthropic.APIError("Fail", request=Mock(), body=None)
    mock_gemini_adapter.side_effect = Exception("Gemini Fail")
    messages = [ChatMessage(role="user", content="Test")]
    with pytest.raises(AllProvidersFailedError):
        await engine.execute_request(
            model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-opus'], 'google_gemini': ['gemini-pro']},
            messages=messages)
    assert mock_guards['openai'].get_resource.call_count == 3
    assert mock_guards['anthropic'].get_resource.call_count == 2
    assert mock_guards['google_gemini'].get_resource.call_count == 2


# --- Content Policy Mitigation Tests ---
@pytest.fixture
def mock_content_policy_details():
    return ErrorDetails(category=ErrorCategory.CONTENT_POLICY, is_retriable=True, provider="openai")


@pytest.mark.asyncio
async def test_content_policy_error_triggers_successful_mitigation(engine_with_rewriter, mock_openai_adapter,
                                                                   mock_rewriter, mocker, mock_content_policy_details):
    engine = engine_with_rewriter
    mocker.patch.object(engine.error_parser, 'classify_error', return_value=mock_content_policy_details)
    mock_openai_adapter.side_effect = [
        openai.BadRequestError("policy", response=Mock(), body={"error": {"code": "content_policy_violation"}}),
        CompletionResponse(success=True, content="Success", latency_ms=100.0)]
    mock_rewriter.rephrase_for_policy_compliance.return_value = [ChatMessage(role="user", content="safe")]
    messages = [ChatMessage(role="user", content="risky")]
    response = await engine.execute_request(model_priority_map={'openai': ['gpt-4o']}, messages=messages)
    assert response.success is True
    assert mock_openai_adapter.call_count == 2


@pytest.mark.asyncio
async def test_mitigation_fails_if_rewriter_fails(engine_with_rewriter, mock_openai_adapter, mock_rewriter, mocker,
                                                  mock_content_policy_details):
    engine = engine_with_rewriter
    mocker.patch.object(engine.error_parser, 'classify_error', return_value=mock_content_policy_details)
    mock_openai_adapter.side_effect = openai.BadRequestError("policy", response=Mock(),
                                                             body={"error": {"code": "content_policy_violation"}})
    mock_rewriter.rephrase_for_policy_compliance.side_effect = RewriteFailedError("LLM fail")
    with pytest.raises(AllProvidersFailedError):
        await engine_with_rewriter.execute_request(
            model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-opus']},
            messages=[ChatMessage(role="user", content="risky")])
    mock_openai_adapter.assert_called_once()


@pytest.mark.asyncio
async def test_mitigation_fails_if_rephrased_prompt_also_fails(engine_with_rewriter, mock_openai_adapter, mock_rewriter,
                                                               mocker, mock_content_policy_details):
    engine = engine_with_rewriter
    mocker.patch.object(engine.error_parser, 'classify_error', return_value=mock_content_policy_details)
    mock_openai_adapter.side_effect = [
        openai.BadRequestError("policy 1", response=Mock(), body={"error": {"code": "content_policy_violation"}}),
        openai.BadRequestError("policy 2", response=Mock(), body={"error": {"code": "content_policy_violation"}})]
    mock_rewriter.rephrase_for_policy_compliance.return_value = [ChatMessage(role="user", content="safe")]
    with pytest.raises(AllProvidersFailedError):
        await engine_with_rewriter.execute_request(
            model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-opus']},
            messages=[ChatMessage(role="user", content="risky")])
    assert mock_openai_adapter.call_count == 2


@pytest.mark.asyncio
async def test_content_policy_error_fails_fast_if_no_rewriter(engine, mock_openai_adapter, mocker,
                                                              mock_content_policy_details):
    mocker.patch.object(engine.error_parser, 'classify_error', return_value=mock_content_policy_details)
    mock_openai_adapter.side_effect = openai.BadRequestError("policy", response=Mock(),
                                                             body={"error": {"code": "content_policy_violation"}})
    with pytest.raises(AllProvidersFailedError):
        await engine.execute_request(model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-opus']},
                                     messages=[ChatMessage(role="user", content="risky")])
    mock_openai_adapter.assert_called_once()


# --- Dynamic Provider Ranking Tests ---
class TestDynamicProviderRanking:
    @pytest.mark.asyncio
    async def test_dynamic_ranking_overrides_static_order(self, engine, mock_ranking_engine, mock_openai_adapter,
                                                          mock_anthropic_adapter):
        mock_ranking_engine.get_ranked_providers.return_value = ["anthropic", "openai"]
        mock_anthropic_adapter.return_value = CompletionResponse(success=True, content="Success from Anthropic",
                                                                 latency_ms=100.0)
        await engine.execute_request(model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-opus']},
                                     messages=[ChatMessage(role="user", content="Test")])
        mock_anthropic_adapter.assert_called_once()
        mock_openai_adapter.assert_not_called()


# --- NEW TEST SUITE: User-Intent First Architecture & Cost Management (Refactored) ---
class TestUserIntentAndCostManagement:

    def _create_success_response(self, content="Success", provider_name="openai", model_used="gpt-4o", latency=100.0,
                                 input_tokens=10, output_tokens=10):
        # Incorporating your fix for TokenUsage
        return CompletionResponse(
            success=True, content=content, model_used=model_used, latency_ms=latency,
            usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens),
            metadata={'provider_name': provider_name}
        )

    @pytest.mark.asyncio
    async def test_preferred_provider_succeeds_immediately(self, engine, mock_openai_adapter, mock_bias_ledger):
        mock_openai_adapter.return_value = self._create_success_response(provider_name="openai", model_used="gpt-4o")
        response = await engine.execute_request(
            model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-sonnet']},
            messages=[ChatMessage(role="user", content="Hello")], preferred_provider="openai")
        assert response.success is True
        mock_openai_adapter.assert_called_once_with([ChatMessage(role="user", content="Hello")],
                                                    api_key_override="key-openai-1", model="gpt-4o")
        kwargs = mock_bias_ledger.log_request_lifecycle.call_args.kwargs
        assert kwargs['initial_selection_mode'] == "PREFERENCE_DRIVEN"
        assert kwargs['failover_reason'] is None

    @pytest.mark.asyncio
    async def test_preferred_provider_circuit_open_falls_back(self, engine, mock_openai_adapter, mock_anthropic_adapter,
                                                              mock_bias_ledger):
        engine.circuit_breakers.get_breaker("openai").check = Mock(
            side_effect=CircuitBreakerError("Circuit for openai is OPEN"))
        mock_anthropic_adapter.return_value = self._create_success_response(provider_name="anthropic",
                                                                            model_used="claude-3-sonnet")
        await engine.execute_request(model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-sonnet']},
                                     messages=[ChatMessage(role="user", content="Hello")], preferred_provider="openai")
        mock_openai_adapter.assert_not_called()
        mock_anthropic_adapter.assert_called_once()
        assert mock_bias_ledger.log_request_lifecycle.call_args.kwargs[
                   'failover_reason'] == "PREFERRED_PROVIDER_CIRCUIT_OPEN:openai"

    @pytest.mark.asyncio
    async def test_preferred_provider_all_keys_unhealthy_falls_back(self, engine, mock_openai_adapter,
                                                                    mock_anthropic_adapter, mock_guards,
                                                                    mock_bias_ledger):
        mock_guards['openai'].has_healthy_resources.return_value = False
        mock_anthropic_adapter.return_value = self._create_success_response(provider_name="anthropic",
                                                                            model_used="claude-3-sonnet")
        await engine.execute_request(model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-sonnet']},
                                     messages=[ChatMessage(role="user", content="Hello")], preferred_provider="openai")
        mock_openai_adapter.assert_not_called()
        mock_anthropic_adapter.assert_called_once()
        assert mock_bias_ledger.log_request_lifecycle.call_args.kwargs[
                   'failover_reason'] == "ALL_PREFERRED_KEYS_UNHEALTHY:openai"

    @pytest.mark.asyncio
    async def test_preferred_provider_all_models_exceed_cost_cap_initial_check_falls_back(self, engine,
                                                                                          mock_openai_adapter,
                                                                                          mock_gemini_adapter,
                                                                                          mock_bias_ledger):
        engine.provider_profiles.profiles['openai']['gpt-4o'].input_cpm = Decimal("10000.00")
        engine.provider_profiles.profiles['anthropic']['claude-3-sonnet'].input_cpm = Decimal("10000.00")
        mock_gemini_adapter.return_value = self._create_success_response(provider_name="google_gemini",
                                                                         model_used="gemini-pro")
        messages = [ChatMessage(role="user", content="Test")]
        await engine.execute_request(
            model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-sonnet'],
                                'google_gemini': ['gemini-pro']},
            messages=messages, preferred_provider="openai", max_estimated_cost_usd=0.01, max_tokens=1
        )
        mock_openai_adapter.assert_not_called()
        mock_gemini_adapter.assert_called_once()
        kwargs = mock_bias_ledger.log_request_lifecycle.call_args.kwargs
        assert kwargs['failover_reason'] == "ALL_PREFERRED_MODELS_EXCEED_COST_CAP_INITIAL_CHECK:openai"

    @pytest.mark.asyncio
    async def test_cost_cap_skips_expensive_model_in_preferred_mode(self, engine, mock_openai_adapter,
                                                                    mock_bias_ledger):
        engine.provider_profiles.profiles['openai']['gpt-4o'].input_cpm = Decimal("1000.00")
        engine.provider_profiles.profiles['openai']['gpt-4o'].output_cpm = Decimal("1000.00")
        engine.provider_profiles.profiles['openai']['gpt-4-turbo'].input_cpm = Decimal("1.0")
        engine.provider_profiles.profiles['openai']['gpt-4-turbo'].output_cpm = Decimal("1.0")
        mock_openai_adapter.return_value = self._create_success_response(provider_name="openai",
                                                                         model_used="gpt-4-turbo")

        response = await engine.execute_request(
            model_priority_map={'openai': ['gpt-4o', 'gpt-4-turbo']},
            messages=[ChatMessage(role="user", content="Test")], preferred_provider="openai",
            max_estimated_cost_usd=0.01
        )
        assert response.success is True
        mock_openai_adapter.assert_called_once_with([ChatMessage(role="user", content="Test")],
                                                    api_key_override="key-openai-1", model="gpt-4-turbo")
        kwargs = mock_bias_ledger.log_request_lifecycle.call_args.kwargs
        assert kwargs['cost_cap_enforced'] is True

    @pytest.mark.asyncio
    async def test_all_providers_fail_due_to_cost_cap(self, engine, mock_openai_adapter, mock_anthropic_adapter,
                                                      mock_bias_ledger):
        engine.provider_profiles.profiles['openai']['gpt-4o'].input_cpm = Decimal("10000.00")
        engine.provider_profiles.profiles['anthropic']['claude-3-sonnet'].input_cpm = Decimal("10000.00")
        with pytest.raises(AllProvidersFailedError):
            await engine.execute_request(
                model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-sonnet']},
                messages=[ChatMessage(role="user", content="Test")], max_estimated_cost_usd=0.000001
            )
        kwargs = mock_bias_ledger.log_request_lifecycle.call_args.kwargs
        assert kwargs['failover_reason'] == "ALL_DYNAMIC_PROVIDERS_FAILED"

    @pytest.mark.asyncio
    async def test_preferred_unhealthy_and_fallback_cost_skips_success(self, engine, mock_anthropic_adapter,
                                                                       mock_gemini_adapter, mock_guards,
                                                                       mock_bias_ledger):
        mock_guards['openai'].has_healthy_resources.return_value = False
        engine.provider_profiles.profiles['anthropic']['claude-3-sonnet'].input_cpm = Decimal("10000.00")
        mock_gemini_adapter.return_value = self._create_success_response(provider_name="google_gemini",
                                                                         model_used="gemini-pro")

        await engine.execute_request(
            model_priority_map={'openai': ['gpt-4o'], 'anthropic': ['claude-3-sonnet'],
                                'google_gemini': ['gemini-pro']},
            messages=[ChatMessage(role="user", content="Test")], preferred_provider="openai",
            max_estimated_cost_usd=0.01, max_tokens=1
        )
        mock_anthropic_adapter.assert_not_called()
        mock_gemini_adapter.assert_called_once()
        kwargs = mock_bias_ledger.log_request_lifecycle.call_args.kwargs
        assert kwargs['failover_reason'] == "ALL_PREFERRED_KEYS_UNHEALTHY:openai"
        assert kwargs['cost_cap_enforced'] is True