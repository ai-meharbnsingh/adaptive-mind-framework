# tests/test_claude_adapter.py

import os

import pytest
from antifragile_framework.providers.api_abstraction_layer import ChatMessage
from antifragile_framework.providers.provider_adapters.claude_adapter import (
    ClaudeProvider,
)
from dotenv import load_dotenv

# --- Test Setup ---

load_dotenv()

claude_api_keys_str = os.getenv("ANTHROPIC_API_KEY")
if claude_api_keys_str:
    CLAUDE_API_KEYS = claude_api_keys_str.split(",")
else:
    CLAUDE_API_KEYS = []

skip_if_no_key = pytest.mark.skipif(
    not CLAUDE_API_KEYS,
    reason="ANTHROPIC_API_KEY environment variable not set.",
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
def claude_provider() -> ClaudeProvider:
    if not CLAUDE_API_KEYS:
        pytest.skip("Skipping Claude provider setup: No API key found.")

    config = {
        "api_key": CLAUDE_API_KEYS[0],
        "default_model": "claude-3-haiku-20240307",
    }
    return ClaudeProvider(config)


# --- Test Cases ---


@skip_if_no_key
@pytest.mark.asyncio
async def test_claude_agenerate_completion_success(
    claude_provider: ClaudeProvider,
):
    messages = [
        ChatMessage(
            role="system",
            content="You are a helpful assistant who provides concise answers.",
        ),
        ChatMessage(
            role="user", content="What is the color of the sky on a clear day?"
        ),
    ]
    response = await claude_provider.agenerate_completion(messages)
    assert response.success is True
    assert "blue" in response.content.lower()


@skip_if_no_key
@pytest.mark.asyncio
async def test_claude_agenerate_no_system_prompt(
    claude_provider: ClaudeProvider,
):
    messages = [
        ChatMessage(
            role="user", content="Simply respond with the word 'test'."
        )
    ]
    response = await claude_provider.agenerate_completion(messages)
    assert response.success is True
    assert "test" in response.content.lower()


@skip_if_no_key
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_model", ["claude-3-5-sonnet-20240620", "claude-3-haiku-20240307"]
)
async def test_claude_model_override(
    claude_provider: ClaudeProvider, test_model: str
):
    messages = [
        ChatMessage(
            role="user", content=f"Confirm you are an Anthropic model."
        )
    ]
    response = await claude_provider.agenerate_completion(
        messages, model=test_model
    )
    assert response.success is True
    assert test_model in response.model_used


@skip_if_no_key
@pytest.mark.asyncio
async def test_claude_bad_request_on_invalid_auth(
    claude_provider: ClaudeProvider,
):
    bad_config = {"api_key": "sk-ant-this_is_a_very_bad_key-12345"}
    bad_provider = ClaudeProvider(bad_config)
    messages = [ChatMessage(role="user", content="This will fail.")]
    response = await bad_provider.agenerate_completion(messages)
    assert response.success is False
    assert "authentication_error" in response.error_message


@skip_if_no_key
@pytest.mark.asyncio
async def test_claude_agenerate_completion_returns_usage(
    claude_provider: ClaudeProvider,
):
    messages = [ChatMessage(role="user", content="What is 3 + 3?")]
    response = await claude_provider.agenerate_completion(messages)

    assert response.success is True
    assert response.usage is not None
    assert isinstance(response.usage.input_tokens, int)
    assert isinstance(response.usage.output_tokens, int)
    assert response.usage.input_tokens > 0
    assert response.usage.output_tokens > 0
