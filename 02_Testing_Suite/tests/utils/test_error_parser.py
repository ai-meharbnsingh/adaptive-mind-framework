# tests/utils/test_error_parser.py

from unittest.mock import Mock

import pytest
from antifragile_framework.utils.error_parser import (
    ErrorCategory,
    ErrorParser,
)

# Safe imports for provider SDKs
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from google.api_core import exceptions as google_exceptions

    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


# --- Mocks for SDK Exceptions ---


def create_mock_response(status_code, headers=None, json_body=None):
    response = Mock()
    response.status_code = status_code
    response.headers = headers or {}
    if json_body:
        response.json.return_value = json_body
    return response


if OPENAI_AVAILABLE:
    mock_openai_rate_limit = openai.RateLimitError(
        "Rate limit",
        response=create_mock_response(429, headers={"retry-after": "20"}),
        body={},
    )
    mock_openai_content_policy = openai.BadRequestError(
        "Content policy",
        response=create_mock_response(400),
        body={"error": {"code": "content_policy_violation"}},
    )
    mock_openai_bad_request = openai.BadRequestError(
        "Invalid request",
        response=create_mock_response(400),
        body={"error": {"code": "invalid_request"}},
    )

if ANTHROPIC_AVAILABLE:
    anthropic_content_policy_body = {
        "error": {
            "type": "invalid_request_error",
            "message": "contains safety violations",
        }
    }
    mock_anthropic_content_policy = anthropic.BadRequestError(
        "Content policy",
        response=create_mock_response(400, json_body=anthropic_content_policy_body),
        body=anthropic_content_policy_body,
    )
    anthropic_bad_request_body = {
        "error": {"type": "invalid_request_error", "message": "Malformed"}
    }
    mock_anthropic_bad_request = anthropic.BadRequestError(
        "Invalid request",
        response=create_mock_response(400, json_body=anthropic_bad_request_body),
        body=anthropic_bad_request_body,
    )


@pytest.fixture
def parser():
    return ErrorParser()


@pytest.mark.skipif(not OPENAI_AVAILABLE, reason="OpenAI SDK not installed")
def test_openai_classification(parser):
    details = parser.classify_error(mock_openai_rate_limit, "openai")
    assert details.category == ErrorCategory.TRANSIENT
    assert details.is_retriable is True
    assert details.retry_after_seconds == 20

    details = parser.classify_error(mock_openai_content_policy, "openai")
    assert details.category == ErrorCategory.CONTENT_POLICY

    details = parser.classify_error(mock_openai_bad_request, "openai")
    assert details.category == ErrorCategory.FATAL


@pytest.mark.skipif(not ANTHROPIC_AVAILABLE, reason="Anthropic SDK not installed")
def test_anthropic_classification(parser):
    details = parser.classify_error(mock_anthropic_content_policy, "anthropic")
    assert details.category == ErrorCategory.CONTENT_POLICY

    details = parser.classify_error(mock_anthropic_bad_request, "anthropic")
    assert details.category == ErrorCategory.FATAL

    rate_limit_error = anthropic.RateLimitError(
        "Rate limit", response=create_mock_response(429), body={}
    )
    details = parser.classify_error(rate_limit_error, "anthropic")
    assert details.category == ErrorCategory.TRANSIENT


@pytest.mark.skipif(not GOOGLE_AVAILABLE, reason="Google SDK not installed")
def test_google_classification(parser):
    transient_error = google_exceptions.ResourceExhausted("Quota")
    details = parser.classify_error(transient_error, "google_gemini")
    assert details.category == ErrorCategory.TRANSIENT

    fatal_error = google_exceptions.PermissionDenied("Permission")
    details = parser.classify_error(fatal_error, "google_gemini")
    assert details.category == ErrorCategory.FATAL


def test_unknown_error_classification(parser):
    unknown_error = ValueError("Something unexpected")
    details = parser.classify_error(unknown_error, "some_provider")
    assert details.category == ErrorCategory.UNKNOWN
