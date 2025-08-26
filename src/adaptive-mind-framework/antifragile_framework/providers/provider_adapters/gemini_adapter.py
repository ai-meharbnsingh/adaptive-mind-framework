# antifragile_framework/providers/provider_adapters/gemini_adapter.py

import os
import time
import logging
import asyncio
import random
import uuid
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from antifragile_framework.providers.api_abstraction_layer import LLMProvider, ChatMessage, CompletionResponse, TokenUsage

log = logging.getLogger(__name__)


def _extract_gemini_usage(response: Any) -> Optional[TokenUsage]:
    """Safely extracts token usage from a Gemini SDK response object."""
    try:
        if response and response.usage_metadata:
            # Gemini uses different field names
            return TokenUsage(
                input_tokens=response.usage_metadata.prompt_token_count,
                output_tokens=response.usage_metadata.candidates_token_count
            )
    except (AttributeError, TypeError) as e:
        log.warning(f"Could not extract token usage from Gemini response: {e}")
    return None


class GeminiProvider(LLMProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_model = self.config.get('default_model', 'gemini-1.5-flash-latest')
        self.primary_api_key = self.config.get('api_key')
        if not self.primary_api_key:
            raise ValueError("Google Gemini 'api_key' not found in the provider configuration.")
        log.info("GeminiProvider initialized.")

    def get_provider_name(self) -> str:
        return "google_gemini"

    async def _generate_mock_response(self, model_to_use: str, start_time: float) -> CompletionResponse:
        """Generates a realistic, mock completion response for performance testing."""
        # Simulate a small, variable I/O delay (5ms to 15ms)
        await asyncio.sleep(random.uniform(0.005, 0.015))

        # Simulate variable token usage
        input_tokens = random.randint(50, 250)
        output_tokens = random.randint(100, 500)
        usage = TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens)

        # Create a unique response content
        content = f"Mocked Gemini response for model {model_to_use}. UUID: {uuid.uuid4().hex[:12]}"

        # Calculate latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        metadata = {"provider_name": self.get_provider_name(), "mock": True}

        return CompletionResponse(
            success=True,
            content=content,
            model_used=model_to_use,
            usage=usage,
            latency_ms=latency_ms,
            error_message=None,
            raw_response={"mock_reason": "PERFORMANCE_TEST_MODE"},
            metadata=metadata
        )

    async def agenerate_completion(
            self, messages: List[ChatMessage], temperature: float = 0.7, max_tokens: int = 2048,
            api_key_override: Optional[str] = None, **kwargs: Any
    ) -> CompletionResponse:
        start_time = time.perf_counter()
        model_to_use = kwargs.get('model', self.default_model)

        # Performance test mocking logic
        # ======================================================================
        # CORRECTED: Check for 'true' instead of 'mock'
        # ======================================================================
        if os.getenv('PERFORMANCE_TEST_MODE', 'False').lower() == 'true':
            return await self._generate_mock_response(model_to_use, start_time)

        # --- Original logic for real API calls ---
        usage = None
        api_key_to_use = api_key_override or self.primary_api_key

        try:
            # Per-call configuration is safer for Gemini
            genai.configure(api_key=api_key_to_use)

            system_instruction, user_assistant_messages_raw = self._prepare_provider_messages(messages)
            if not user_assistant_messages_raw:
                return CompletionResponse(success=False, latency_ms=0,
                                          error_message="Cannot make a provider call with no user/assistant messages.")

            formatted_messages = []
            for msg in user_assistant_messages_raw:
                role = "model" if msg["role"] == "assistant" else msg["role"]
                formatted_messages.append({"role": role, "parts": [msg["content"]]})

            model = genai.GenerativeModel(
                model_name=model_to_use,
                system_instruction=system_instruction or None
            )

            generation_config = genai.types.GenerationConfig(max_output_tokens=max_tokens, temperature=temperature)

            response = await model.generate_content_async(
                formatted_messages,
                generation_config=generation_config
            )
            latency_ms = (time.perf_counter() - start_time) * 1000

            if not response.candidates or not hasattr(response, 'text') or not response.text:
                finish_reason = response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN"
                safety_ratings = str(getattr(response, 'prompt_feedback', {}).get('safety_ratings', 'N/A'))
                error_msg = f"Gemini response was empty or blocked. Finish Reason: {finish_reason}."
                return CompletionResponse(success=False, content=None, model_used=model_to_use, latency_ms=latency_ms,
                                          error_message=error_msg,
                                          metadata={"finish_reason": finish_reason, "safety_ratings": safety_ratings})

            content = response.text
            usage = _extract_gemini_usage(response)
            metadata = {"provider_name": self.get_provider_name()}

            return CompletionResponse(success=True, content=content, model_used=model_to_use, usage=usage,
                                      latency_ms=latency_ms, error_message=None, metadata=metadata)

        except google_exceptions.PermissionDenied as e:
            error_msg = f"Google Gemini API Error: Your API key is invalid. Details: {getattr(e, 'message', str(e))}"
        except google_exceptions.GoogleAPICallError as e:
            error_msg = f"Google Gemini API Error: {getattr(e, 'message', str(e))}"
        except Exception as e:
            error_msg = f"An unexpected error occurred with Google Gemini: {str(e)}"
            log.exception("Unexpected Google Gemini Error")

        latency_ms = (time.perf_counter() - start_time) * 1000
        log.error(f"Failed Google Gemini call for model {model_to_use}. Reason: {error_msg}")
        return CompletionResponse(success=False, content=None, model_used=model_to_use, latency_ms=latency_ms,
                                  error_message=error_msg)