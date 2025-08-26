# tests/test_gemini_adapter.py

import os

import pytest
from antifragile_framework.providers.api_abstraction_layer import ChatMessage
from antifragile_framework.providers.provider_adapters.gemini_adapter import (
    GeminiProvider,
)
from dotenv import load_dotenv

# --- Test Setup ---

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

skip_if_no_key = pytest.mark.skipif(
    not gemini_api_key, reason="GEMINI_API_KEY environment variable not set."
)


# ==============================================================================
# FIX: Fixture to ensure tests run in "production" mode (no mocking)
# ==============================================================================
@pytest.fixture(autouse=True)
def force_prod_mode(monkeypatch):
    """
    Temporarily removes the PERFORMANCE_TEST_MODE environment variable for this
    test module, ensuring that real API calls are made.
    """
    if "PERFORMANCE_TEST_MODE" in os.environ:
        monkeypatch.delenv("PERFORMANCE_TEST_MODE")


@pytest.fixture
def gemini_provider() -> GeminiProvider:
    """A pytest fixture to create an instance of the GeminiProvider for testing."""
    if not gemini_api_key:
        pytest.skip("Skipping Gemini provider setup: No API key found.")

    config = {
        "api_key": gemini_api_key.split(",")[
            0
        ],  # Use the first key if multiple are present
        "default_model": "gemini-1.5-flash-latest",
    }
    return GeminiProvider(config)


# --- Test Cases ---


@skip_if_no_key
@pytest.mark.asyncio
async def test_gemini_agenerate_completion_success(
    gemini_provider: GeminiProvider,
):
    messages = [
        ChatMessage(
            role="user",
            content="What is the main component of Earth's atmosphere?",
        )
    ]
    response = await gemini_provider.agenerate_completion(messages)
    assert response.success is True
    assert "nitrogen" in response.content.lower()


@skip_if_no_key
@pytest.mark.asyncio
async def test_gemini_with_system_prompt(gemini_provider: GeminiProvider):
    messages = [
        ChatMessage(
            role="system",
            content="You are a poet. Respond only with a two-line rhyming poem.",
        ),
        ChatMessage(role="user", content="Write a short poem about the moon."),
    ]
    response = await gemini_provider.agenerate_completion(messages, temperature=0.5)
    assert response.success is True
    assert len(response.content.strip().split("\n")) >= 2


@skip_if_no_key
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_model", ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest"]
)
async def test_gemini_model_override(gemini_provider: GeminiProvider, test_model: str):
    messages = [ChatMessage(role="user", content="Confirm you are a Google model.")]
    response = await gemini_provider.agenerate_completion(messages, model=test_model)
    assert response.success is True
    assert "google" in response.content.lower()


@skip_if_no_key
@pytest.mark.asyncio
async def test_gemini_bad_request_on_invalid_auth(
    gemini_provider: GeminiProvider,
):
    """
    Tests how the adapter handles a specific, predictable API error (bad API key).
    """
    bad_config = {"api_key": "this-is-a-very-bad-google-api-key-12345"}
    bad_provider = GeminiProvider(bad_config)
    messages = [ChatMessage(role="user", content="This will fail.")]
    response = await bad_provider.agenerate_completion(messages)
    assert response.success is False
    assert response.content is None
    # ==============================================================================
    # FIX: Loosened assertion to be more robust against minor error message changes
    # ==============================================================================
    assert "api key not valid" in response.error_message.lower()


@skip_if_no_key
@pytest.mark.asyncio
async def test_gemini_agenerate_completion_returns_usage(
    gemini_provider: GeminiProvider,
):
    """Verify that a successful completion response includes token usage data."""
    messages = [ChatMessage(role="user", content="What is 4 + 4?")]
    response = await gemini_provider.agenerate_completion(messages)

    assert response.success is True
    assert response.usage is not None
    assert isinstance(response.usage.input_tokens, int)
    assert isinstance(response.usage.output_tokens, int)
    assert response.usage.input_tokens > 0
    # Gemini sometimes returns 0 for output_tokens on very short answers, so we allow it
    assert response.usage.output_tokens >= 0
