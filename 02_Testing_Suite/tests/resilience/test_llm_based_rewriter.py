# tests/resilience/test_llm_based_rewriter.py

from unittest.mock import AsyncMock, Mock

import pytest
from antifragile_framework.core.exceptions import RewriteFailedError
from antifragile_framework.providers.api_abstraction_layer import (
    ChatMessage,
    CompletionResponse,
    LLMProvider,
)
from antifragile_framework.resilience.llm_based_rewriter import (
    LLMBasedRewriter,
)


@pytest.fixture
def mock_llm_client():
    client = Mock(spec=LLMProvider)
    client.agenerate_completion = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_rewriter_initialization(mock_llm_client):
    """Tests that the rewriter initializes correctly."""
    rewriter = LLMBasedRewriter(llm_client=mock_llm_client, model="test-model")
    assert rewriter.llm_client is mock_llm_client
    assert rewriter.model == "test-model"
    with pytest.raises(TypeError):
        LLMBasedRewriter(llm_client="not a client")


@pytest.mark.asyncio
async def test_rephrase_success(mock_llm_client):
    """Tests the successful rephrasing of a user prompt."""
    rephrased_text = "This is the neutralized content."
    mock_llm_client.agenerate_completion.return_value = CompletionResponse(
        success=True,
        content=rephrased_text,
        provider_name="mock_provider",
        model="test-model",
        latency_ms=100.0,
    )

    rewriter = LLMBasedRewriter(llm_client=mock_llm_client)
    original_messages = [
        ChatMessage(role="system", content="You are a helpful assistant."),
        ChatMessage(role="user", content="This is the original content."),
    ]

    new_messages = await rewriter.rephrase_for_policy_compliance(
        original_messages
    )

    mock_llm_client.agenerate_completion.assert_awaited_once()

    the_call = mock_llm_client.agenerate_completion.call_args
    meta_prompt = the_call.kwargs["messages"]

    assert "rephrase" in meta_prompt[0].content.lower()
    assert original_messages[1].content in meta_prompt[1].content
    assert original_messages[1].content == "This is the original content."
    assert new_messages[0].content == original_messages[0].content
    assert new_messages[1].content == rephrased_text


@pytest.mark.asyncio
async def test_rephrase_api_call_fails(mock_llm_client):
    mock_llm_client.agenerate_completion.return_value = CompletionResponse(
        success=False,
        error_message="API limit reached",
        provider_name="mock_provider",
        model="test-model",
        latency_ms=50.0,
    )

    rewriter = LLMBasedRewriter(llm_client=mock_llm_client)
    messages = [ChatMessage(role="user", content="Test")]

    with pytest.raises(RewriteFailedError, match="API limit reached"):
        await rewriter.rephrase_for_policy_compliance(messages)


@pytest.mark.asyncio
async def test_rephrase_raises_on_no_user_content(mock_llm_client):
    rewriter = LLMBasedRewriter(llm_client=mock_llm_client)
    messages = [ChatMessage(role="system", content="System instruction only")]

    with pytest.raises(RewriteFailedError, match="No user content found"):
        await rewriter.rephrase_for_policy_compliance(messages)
