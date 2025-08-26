# tests/api/test_e2e_resilience.py

import logging
from copy import deepcopy
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, call

import anthropic
import openai
import pytest
import pytest_asyncio
from antifragile_framework.api.framework_api import app
from antifragile_framework.config.config_loader import load_provider_profiles
from antifragile_framework.core.exceptions import ContentPolicyError
from antifragile_framework.providers.api_abstraction_layer import (
    ChatMessage,
    CompletionResponse,
)
from antifragile_framework.resilience.prompt_rewriter import PromptRewriter
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncClient:
    """
    Fixture that creates a new app instance for each test function,
    ensuring state isolation and proper lifespan management.
    """
    # Ensure a fresh state for each test run by clearing state that lifespan sets
    app.state.failover_engine = None
    app.state.event_bus = None
    app.state.provider_ranking_engine = None
    app.state.telemetry_subscriber = None

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client


@pytest.fixture(scope="module")
def mock_provider_profiles():
    """Provides a consistent, mock set of provider profiles for tests."""
    return load_provider_profiles()


class TestE2EHappyPathAndFailover:
    @pytest.mark.asyncio
    async def test_happy_path_successful_request(
        self, async_client: AsyncClient, mocker
    ):
        mock_agenerate = mocker.patch(
            "antifragile_framework.providers.provider_adapters.openai_adapter.OpenAIProvider.agenerate_completion",
            new_callable=AsyncMock,
        )
        mock_agenerate.return_value = CompletionResponse(
            success=True,
            content="This is a successful test response.",
            model_used="gpt-4o",
            latency_ms=123.45,
        )
        request_payload = {
            "model_priority_map": {"openai": ["gpt-4o"]},
            "messages": [{"role": "user", "content": "Hello, world!"}],
        }
        response = await async_client.post(
            "/v1/chat/completions", json=request_payload
        )
        assert response.status_code == 200
        assert (
            response.json()["content"] == "This is a successful test response."
        )
        mock_agenerate.assert_called_once()

    @pytest.mark.asyncio
    async def test_resilience_succeeds_on_last_available_provider(
        self, async_client: AsyncClient, mocker
    ):
        mocker.patch(
            "antifragile_framework.providers.provider_adapters.openai_adapter.OpenAIProvider.agenerate_completion",
            new_callable=AsyncMock,
            side_effect=openai.APIError(
                "OpenAI is down", request=mocker.Mock(), body=None
            ),
        )
        mocker.patch(
            "antifragile_framework.providers.provider_adapters.claude_adapter.ClaudeProvider.agenerate_completion",
            new_callable=AsyncMock,
            side_effect=anthropic.APIError(
                "Anthropic is down", request=mocker.Mock(), body=None
            ),
        )
        mock_gemini = mocker.patch(
            "antifragile_framework.providers.provider_adapters.gemini_adapter.GeminiProvider.agenerate_completion",
            new_callable=AsyncMock,
            return_value=CompletionResponse(
                success=True,
                content="Success from Gemini!",
                model_used="gemini-1.5-flash-latest",
                latency_ms=300.0,
                metadata={"provider_name": "google_gemini"},
            ),
        )
        request_payload = {
            "model_priority_map": {
                "openai": ["gpt-4o"],
                "anthropic": ["claude-3-opus-20240229"],
                "google_gemini": ["gemini-1.5-flash-latest"],
            },
            "messages": [{"role": "user", "content": "Test resilience"}],
        }
        response = await async_client.post(
            "/v1/chat/completions", json=request_payload
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Success from Gemini!"
        mock_gemini.assert_called_once()


class TestE2ECostCapping:
    @pytest.mark.parametrize(
        "scenario",
        [
            {
                "id": "skip_one_and_succeed",
                "max_cost": 0.01,
                "expected_status": 200,
                "expected_content": "Success from Gemini!",
                "openai_should_be_called": False,
            },
            {
                "id": "skip_all_and_fail",
                "max_cost": 0.0001,
                "expected_status": 503,
                "expected_content": None,
                "openai_should_be_called": False,
            },
            {
                "id": "no_skipping",
                "max_cost": 999.0,
                "expected_status": 200,
                "expected_content": "Success from OpenAI!",
                "openai_should_be_called": True,
            },
        ],
    )
    @pytest.mark.asyncio
    async def test_cost_capping_scenarios(
        self,
        scenario,
        async_client: AsyncClient,
        mocker,
        caplog,
        mock_provider_profiles,
    ):
        caplog.set_level(logging.DEBUG)
        original_profiles = app.state.failover_engine.provider_profiles
        test_profiles = deepcopy(mock_provider_profiles)
        # Make both primary providers expensive
        test_profiles.profiles["openai"]["gpt-4o"].input_cpm = Decimal(
            "100000.00"
        )
        test_profiles.profiles["anthropic"][
            "claude-3-opus-20240229"
        ].input_cpm = Decimal("100000.00")
        app.state.failover_engine.provider_profiles = test_profiles

        mock_openai = mocker.patch(
            "antifragile_framework.providers.provider_adapters.openai_adapter.OpenAIProvider.agenerate_completion",
            new_callable=AsyncMock,
            return_value=CompletionResponse(
                success=True,
                content="Success from OpenAI!",
                model_used="gpt-4o",
                latency_ms=100.0,
            ),
        )
        mocker.patch(
            "antifragile_framework.providers.provider_adapters.claude_adapter.ClaudeProvider.agenerate_completion",
            new_callable=AsyncMock,
            return_value=CompletionResponse(
                success=True,
                content="Success from Anthropic!",
                model_used="claude-3-opus-20240229",
                latency_ms=100.0,
            ),
        )
        # The cheap provider that should succeed
        mocker.patch(
            "antifragile_framework.providers.provider_adapters.gemini_adapter.GeminiProvider.agenerate_completion",
            new_callable=AsyncMock,
            return_value=CompletionResponse(
                success=True,
                content="Success from Gemini!",
                model_used="gemini-1.5-flash-latest",
                latency_ms=100.0,
            ),
        )

        request_payload = {
            "model_priority_map": {
                "openai": ["gpt-4o"],
                "google_gemini": ["gemini-1.5-flash-latest"],
            },
            "messages": [{"role": "user", "content": "Hello"}],
            "max_estimated_cost_usd": scenario["max_cost"],
        }

        response = await async_client.post(
            "/v1/chat/completions", json=request_payload
        )

        assert response.status_code == scenario["expected_status"]
        if response.is_success:
            assert response.json()["content"] == scenario["expected_content"]
        if scenario["openai_should_be_called"]:
            mock_openai.assert_called_once()
        else:
            mock_openai.assert_not_called()

        app.state.failover_engine.provider_profiles = original_profiles


class TestE2EContentPolicy:
    @pytest.mark.asyncio
    async def test_content_policy_mitigation_and_retry(
        self, async_client: AsyncClient, mocker
    ):
        # Arrange
        original_messages = [
            ChatMessage(role="user", content="A risky prompt")
        ]
        safe_messages = [
            ChatMessage(role="user", content="A rephrased safe prompt")
        ]

        realistic_error = openai.BadRequestError(
            "Your request was rejected as a result of our safety system.",
            response=mocker.Mock(),
            body={"error": {"code": "content_policy_violation"}},
        )
        mock_provider = mocker.patch(
            "antifragile_framework.providers.provider_adapters.openai_adapter.OpenAIProvider.agenerate_completion",
            new_callable=AsyncMock,
            side_effect=[
                realistic_error,
                CompletionResponse(
                    success=True,
                    content="Success after rephrasing",
                    model_used="gpt-4o",
                    latency_ms=100.0,
                ),
            ],
        )

        mock_rewriter = MagicMock(spec=PromptRewriter)
        mock_rewriter.rephrase_for_policy_compliance = AsyncMock(
            return_value=safe_messages
        )
        original_rewriter = app.state.failover_engine.prompt_rewriter
        app.state.failover_engine.prompt_rewriter = mock_rewriter

        request_payload = {
            "model_priority_map": {"openai": ["gpt-4o"]},
            "messages": [{"role": "user", "content": "A risky prompt"}],
        }

        # Act
        response = await async_client.post(
            "/v1/chat/completions", json=request_payload
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["content"] == "Success after rephrasing"
        mock_rewriter.rephrase_for_policy_compliance.assert_called_once_with(
            original_messages
        )

        # Teardown
        app.state.failover_engine.prompt_rewriter = original_rewriter
