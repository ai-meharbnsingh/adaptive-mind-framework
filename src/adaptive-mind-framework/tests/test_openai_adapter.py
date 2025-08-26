# tests/test_openai_adapter.py

import os
import pytest
from dotenv import load_dotenv

from antifragile_framework.providers.api_abstraction_layer import ChatMessage
from antifragile_framework.providers.provider_adapters.openai_adapter import OpenAIProvider

# --- Test Setup ---

load_dotenv()

# CORRECTED: The variable name is now OPENAI_API_KEY (singular) to match the .env file
openai_api_keys_str = os.getenv("OPENAI_API_KEY")
if openai_api_keys_str:
    OPENAI_API_KEYS = openai_api_keys_str.split(',')
else:
    OPENAI_API_KEYS = []

skip_if_no_key = pytest.mark.skipif(
    not OPENAI_API_KEYS, reason="OPENAI_API_KEY environment variable not set."
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

@pytest.fixture(scope="module")
def openai_provider() -> OpenAIProvider:
    if not OPENAI_API_KEYS:
        pytest.skip("Skipping OpenAI provider setup: No API key found.")

    config = {
        "api_key": OPENAI_API_KEYS[0],
        "default_model": "gpt-3.5-turbo"
    }
    return OpenAIProvider(config)


# --- Test Cases ---

@skip_if_no_key
@pytest.mark.asyncio
async def test_openai_agenerate_completion_success(openai_provider: OpenAIProvider):
    messages = [
        ChatMessage(role="system", content="You are a helpful assistant."),
        ChatMessage(role="user", content="What is the capital of France?")
    ]
    response = await openai_provider.agenerate_completion(messages)
    assert response.success is True
    assert isinstance(response.content, str)
    assert "Paris" in response.content
    assert response.latency_ms > 0


@skip_if_no_key
@pytest.mark.asyncio
@pytest.mark.parametrize("test_model", ["gpt-4o", "gpt-3.5-turbo"])
async def test_openai_model_override(openai_provider: OpenAIProvider, test_model: str):
    messages = [ChatMessage(role="user", content=f"Confirm you are based on the {test_model} architecture.")]
    response = await openai_provider.agenerate_completion(messages, model=test_model)
    assert response.success is True
    assert isinstance(response.content, str)
    assert test_model in response.model_used.lower()


@pytest.mark.asyncio
async def test_chat_message_validation_failure():
    with pytest.raises(ValueError, match="Message 'content' cannot be empty or just whitespace"):
        ChatMessage(role="user", content="  ")


@skip_if_no_key
@pytest.mark.asyncio
async def test_openai_bad_request_on_invalid_auth(openai_provider: OpenAIProvider):
    """
    Tests how the adapter handles a specific, predictable API error (bad API key).
    """
    bad_config = {"api_key": "sk-this_is_a_bad_key"}
    bad_provider = OpenAIProvider(bad_config)
    messages = [ChatMessage(role="user", content="This will fail.")]
    response = await bad_provider.agenerate_completion(messages)
    assert response.success is False
    assert response.content is None
    # ==============================================================================
    # FIX: Loosened assertion to be more robust against minor error message changes
    # ==============================================================================
    assert "invalid_api_key" in response.error_message or "Incorrect API key" in response.error_message


@skip_if_no_key
@pytest.mark.asyncio
async def test_openai_agenerate_completion_returns_usage(openai_provider: OpenAIProvider):
    """Verify that a successful completion response includes token usage data."""
    messages = [ChatMessage(role="user", content="What is 2 + 2?")]
    response = await openai_provider.agenerate_completion(messages)

    assert response.success is True
    assert response.usage is not None
    assert isinstance(response.usage.input_tokens, int)
    assert isinstance(response.usage.output_tokens, int)
    assert response.usage.input_tokens > 0
    assert response.usage.output_tokens > 0