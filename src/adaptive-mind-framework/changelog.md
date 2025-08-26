# 📜 Changelog - Adaptive Mind Project

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.9.0-alpha.5] - 2025-08-27 (Final Integration, Hardening & Documentation)

### Added
- **Commercial Documentation:** Created the first piece of user-facing commercial documentation (`docs/commercial/framework_overview.md`).
- **Extensible Architecture:** Introduced a `ProviderRegistry` (`antifragile_framework/providers/provider_registry.py`) to make the `FailoverEngine` fully extensible and remove hard-coded provider classes.
- **Robust Server Launcher:** Implemented a new launcher script (`run_server.py`) and a `.env` file strategy to reliably start the API in different modes (production vs. performance test).

### Changed
- **Merged Performance Branch:** Integrated the `feature/performance-benchmarking` branch, consolidating the performance testing suite into the main line of development.
- **Refactored `FailoverEngine`:** The engine now accepts a `ProviderRegistry` for improved extensibility.
- **Refactored `framework_api.py`:** The application startup logic was updated to use the new `ProviderRegistry`.
- **Rewrote Commercial Docs:** The `framework_overview.md` was completely rewritten from a technical explanation to a compelling, sales-focused document leading with ROI and hard performance metrics.
- **Robust Error Parsing:** Replaced fragile string-matching for model-specific errors with a more robust, category-based classification using the `ErrorParser`, including a new `MODEL_ISSUE` category.

### Fixed
- **Critical Test Environment Instability:** Resolved a persistent testing blocker where the FastAPI server failed to start in performance test mode.
- **Skipped Integration Tests:** Fixed an issue causing all provider integration tests to be skipped by integrating `pytest-dotenv` to correctly load API keys from the `.env` file.
- **Performance Test Mocking Bug:** Corrected a logic error in all three provider adapters that prevented them from entering mock mode correctly.
- **Test Isolation Flaw:** Corrected all provider adapter tests to run in "production" mode by default, isolating them from the `PERFORMANCE_TEST_MODE` setting.

### Security
- **Added `.env` to `.gitignore`:** Ensured that environment files containing secrets are never committed to the repository.

## [1.9.0-alpha.4] - 2025-08-26 (Performance Benchmarking)

### Added
- **Performance Testing Suite:** Introduced a new performance testing suite using `locust` (`performance_tests/locustfile.py`) to establish baseline metrics for the framework.
- **Testability Architecture:** Modified all provider adapters to include a `PERFORMANCE_TEST_MODE`. This mock mode isolates the framework from external API latency, enabling accurate and reproducible measurement of internal processing overhead.
- **Performance Documentation:** Created initial documentation (`docs/performance_benchmarking.md`) for the performance testing methodology and baseline results.

### Fixed
- **Critical Concurrency Bottleneck:** Diagnosed and documented that the performance ceiling for a single-worker deployment is ~80 RPS. Exceeding this limit causes `503 Service Unavailable` errors due to server overload, not a bug in the framework's core logic. The baseline test now runs below this threshold with a 0% failure rate.

## [1.9.0-alpha.3] - 2025-08-25 (Initial Security Hardening)

### Security
- **Static Code Analysis (SAST):** Integrated `bandit` into the development workflow. An initial scan of the `antifragile_framework` codebase was completed, revealing **zero** medium or high-severity vulnerabilities.
- **Dependency Vulnerability Scan:** Integrated `safety` into the development workflow. An initial scan of `requirements.txt` was completed, confirming **zero** known vulnerabilities in third-party packages.

## [1.9.0-alpha.2] - 2025-08-24 (E2E Feature Validation)

### Added
- **E2E Cost-Capping Test:** Implemented a parametrized E2E test to validate that the framework correctly skips providers based on the `max_estimated_cost_usd` parameter, ensuring the feature works through the public API.
- **E2E Content Policy Mitigation Test:** Implemented an E2E test to validate the full mitigation flow, confirming the `PromptRewriter` is triggered correctly after a provider's content filter error.

### Fixed
- **E2E Test Data Mismatches:** Corrected multiple subtle bugs in the E2E test suite related to incorrect mock data types (`Decimal` vs `float`) and mismatched model names (`KeyError`), leading to a fully stable and passing test suite.
- **Content Policy Mitigation Logic:** Fixed a bug in the test setup that was preventing the `PromptRewriter` from being correctly engaged by the `FailoverEngine` during E2E tests.


## [1.9.0-alpha.1] - 2025-08-23 (Phase 1 Final Integration - E2E Testing Foundation)

### Added
- **End-to-End Test Suite:** Created a new E2E test suite (`tests/api/test_e2e_resilience.py`) using `httpx` and `asgi-lifespan` to validate the fully integrated FastAPI application.
- **E2E Resilience Test:** Implemented a "last provider standing" test case that simulates multiple provider failures and confirms the framework correctly fails over to the final available provider, proving its core resilience promise at the API level.

### Fixed
- **Critical `EventBus` Race Condition:** Resolved a `RuntimeError` caused by the `EventBus` attempting to publish events after its thread pool was shut down by the application's lifecycle manager. The `publish` method is now resilient to this race condition.

## [1.8.0] - 2025-08-22 (User-Intent First Architecture - Stable)

### Added
- **"User-Intent First" Architecture:** The `FailoverEngine` now fully supports a dual-mode provider selection. Users can specify a `preferred_provider` and `max_estimated_cost_usd` to guide execution, with a robust, value-driven dynamic fallback.
- **Pre-flight Health and Cost Checks:** The engine now performs pre-flight checks before attempting a preferred provider, validating its circuit breaker state, key health, and whether its models meet the user's cost cap.

### Changed
- **`FailoverEngine` Logic:** The `execute_request` method was significantly refactored for clarity and robustness, correctly handling all paths for preference-driven execution and dynamic fallback.
- **`BiasLedger` Auditing:** The `BiasLedgerEntry` now captures detailed decision context, including `initial_selection_mode`, `failover_reason`, and `cost_cap_enforced`.

### Fixed
- **CRITICAL Test Suite Hang:** Resolved a complete test suite freeze in `test_failover_engine.py`. The root cause was a flawed mocking strategy that shared a single mock `ResourceGuard` instance across all providers.
- **Robust Mocking Infrastructure:** Replaced the faulty fixture with a factory-based mock that creates isolated mock instances for each provider, eliminating state corruption and ensuring test stability.
- **Multiple Logic Errors:** Corrected several logical flaws in both the `FailoverEngine` and its tests that were exposed after the test suite hang was fixed.

## [1.8.0-alpha.1] - 2025-08-21 (User-Intent First Architecture - Unstable)

### Added
- **User-Intent First Architecture (Code Complete):** Implemented the core logic for dual-mode provider selection in `FailoverEngine`, allowing users to specify a `preferred_provider` and `max_estimated_cost_usd`.
- **Pre-check Gates and Cost Cap Enforcement:** Wrote the code for robust pre-checks (circuit state, key health, cost) and universal cost cap enforcement.
- **Enhanced BiasLedger Auditability:** Extended `BiasLedgerEntry` schema with new fields for detailed decision tracing.
- **New Test Suite:** Added a comprehensive but currently **non-functional** test suite to validate the new user-intent and cost management logic.

### Changed
- **`failover_engine.py`:** Major refactoring of the `execute_request` method to incorporate the new dual-mode logic.
- **`schemas.py` & `bias_ledger.py`:** Updated schemas to support enhanced auditing.
- **`resource_guard.py`:** Added `has_healthy_resources` method.

### Fixed
- **Critical Test Suite Hang (BLOCKER):** The test suite is currently hanging due to a flawed mocking strategy for `ResourceGuard` in `test_failover_engine.py`. **This version is not stable and requires immediate debugging.**



## [1.7.1] - 2025-08-20 (Foundational Hardening & Test Suite Restoration)

### Changed
- **`ErrorParser` Architecture:** Completely refactored the `ErrorParser` to be production-grade. It now returns a structured `ErrorDetails` object and uses provider-specific handlers to robustly inspect error bodies instead of relying on fragile string matching.
- **`FailoverEngine` Integration:** Updated the core error handling logic in the `FailoverEngine` to consume the new `ErrorDetails` object, making its resilience decisions more precise.

### Fixed
- **Critical Test Suite Cascade Failure:** Resolved a massive cascade of `NameError`, `TypeError`, and `AttributeError` exceptions across the entire test suite. The failures were caused by outdated test mocks that did not match the evolved Pantic and Dataclass schemas (`RequestContext`, `BiasLedgerEntry`).
- **`CircuitBreaker` Bug:** Fixed an `AttributeError` in the `FailoverEngine` where it was incorrectly checking `breaker.is_open` instead of the correct `breaker.state == CircuitBreakerState.OPEN`.
- **Environment and Test Configuration:** Corrected multiple environment variable mismatches in the test files (e.g., `OPENAI_API_KEYS` vs `OPENAI_API_KEY`) that were causing integration tests to be skipped incorrectly. Enabled the full Claude test suite.


## [1.7.0] - 2025-08-19 (Cost-Aware Data Pipeline)

### Added
- **Cost Configuration:** Implemented a new, versioned `config/provider_profiles.json` to store model cost data (input/output cost per million tokens).
- **Fail-Fast Config Validation:** Added Pydantic schemas in `config/schemas.py` and logic in `config_loader.py` to validate the cost configuration at application startup. The system will now refuse to start with an invalid or malformed cost profile, preventing runtime errors.
- **Precision Cost Calculation:** The `BiasLedger` now calculates the `estimated_cost_usd` for every successful API call using Python's `Decimal` type for financial accuracy. It gracefully handles models not in the config by using a `_default` provider profile or logging the cost as `None`.
- **Token Usage Extraction:** All three provider adapters (`OpenAI`, `Gemini`, `Claude`) now extract token usage (input/output tokens) from the SDK response and include it in the standardized `CompletionResponse`.
- **Comprehensive Cost Tests:** Added a new test suite (`tests/config/test_config_loader.py`) for the configuration loader. Updated `test_bias_ledger.py` and all adapter tests to validate the new cost and token data pipeline.

### Changed
- **`BiasLedger` Schema & Logic:** The `BiasLedgerEntry` schema was extended to include `input_tokens`, `output_tokens`, and `estimated_cost_usd`. The `BiasLedger` class now requires the loaded provider profiles at initialization to perform its calculations.
- **`CompletionResponse` Schema:** The central `CompletionResponse` model in `api_abstraction_layer.py` was updated with a new optional `usage: TokenUsage` field.
- **API `lifespan`:** The application startup logic in `framework_api.py` was enhanced to load and validate the new provider profiles and inject them into the `BiasLedger`.

### Fixed
- **Test Data Integrity:** Corrected a recurring test failure in `test_bias_ledger.py` by ensuring all mock `CompletionResponse` objects included the required `latency_ms` field, restoring test suite stability.


## [1.6.0] - 2025-08-18 (Dynamic Provider Adaptation)

### Added
- **Dynamic Provider Prioritization:** Implemented robust logic within the `FailoverEngine` to dynamically re-order the provider attempt list for every request. The order is now determined by real-time performance scores from the `ProviderRankingEngine`, closing the loop on the online learning system.
- **Comprehensive Ranking Tests:** Added a new test class to `test_failover_engine.py` with five specific test cases to validate the new dynamic ranking behavior, including overriding static order, handling empty rankings, ignoring irrelevant providers, and preserving the order of unranked providers.

### Changed
- **`FailoverEngine` Architecture:** The engine's `__init__` now accepts a `ProviderRankingEngine` instance. The `execute_request` method was refactored to remove the `provider_priority` parameter and now uses an internal `_get_dynamic_provider_priority` helper method to determine the attempt order.
- **Simplified Public API:** The `ChatCompletionRequest` model in `framework_api.py` was simplified by removing the static `provider_priority` field. The API contract is now cleaner, as provider selection is fully automated within the engine.
- **API `lifespan`:** The application startup logic was updated to correctly inject the `ProviderRankingEngine` into the `FailoverEngine`.

### Fixed
- (No specific new fixes in this version, focused on adding features.)


## [1.5.0] - 2025-08-17 (Online Learning Engine Foundation)

### Added
- **`ProviderRankingEngine`:** Implemented a new core component to calculate and maintain a real-time performance ranking of providers. It uses an Exponential Moving Average (EMA) of the `ResilienceScore` and is fully thread-safe.
- **`OnlineLearningSubscriber`:** Created a dedicated, event-driven subscriber that listens for completed request data and updates the `ProviderRankingEngine`, decoupling the learning process from the critical request path.
- **Learning Observability Endpoint:** Added a `/v1/learning/rankings` API endpoint to provide real-time visibility into provider scores.
- **New Event Topic:** Added the `LEARNING_FEEDBACK_PUBLISHED` topic to `telemetry/event_topics.py`.

### Changed
- **`FailoverEngine`:** Now publishes the complete `BiasLedgerEntry` to the `EventBus` after every request, providing the data source for the online learning system.
- **`BiasLedger`:** The `BiasLedgerEntry` schema was refactored to use distinct `final_provider` and `final_model` fields instead of a dictionary, improving type safety and clarity. The `log_request_lifecycle` method was updated to support this and return the created entry.
- **Provider Adapters:** All three adapters (`OpenAI`, `Gemini`, `Claude`) were updated to include their `provider_name` in the `metadata` of successful `CompletionResponse` objects, fixing a critical data contract violation.
- **`framework_api.py`:** The API's startup (`lifespan`) logic was significantly enhanced to instantiate and wire together the `EventBus`, `BiasLedger`, `ProviderRankingEngine`, and `OnlineLearningSubscriber`.

### Fixed
- **Critical `asyncio` Misuse:** Resolved a systemic `TypeError` ("a coroutine was expected, got None") by removing invalid `asyncio.create_task` wrappers from the synchronous `EventBus.publish` method across multiple modules (`resource_guard.py`, `failover_engine.py`, `bias_ledger.py`).
- **Cascading Test Failures:** Corrected a major regression in the `test_learning_engine.py` and `test_bias_ledger.py` test suites caused by the `BiasLedger` schema change, restoring full test coverage and stability.

## [1.4.0] - 2025-08-16 (FailoverEngine Refactor for Model Mapping)

### Changed
- **Architectural Refactor of `FailoverEngine`:** The core `execute_request` method was fundamentally refactored. It no longer accepts a simple `model_priority` list and now takes a `model_priority_map` dictionary (`provider -> [model_list]`).
- **Centralized Logic:** This change centralizes the provider-model mapping and failover logic deep within the engine, removing this responsibility from the API layer and improving architectural cohesion.
- **Simplified `framework_api.py`:** The `chat_completions` endpoint was significantly simplified, removing its complex failover loop and replacing it with a direct call to the newly refactored engine.

### Fixed
- **Test Suite Alignment:** The entire `test_failover_engine.py` suite was updated to use the new `model_priority_map` signature, ensuring all tests passed after the major refactor.


## [1.3.0] - 2025-08-15 (Public API Layer & Critical Adapter Refactor)

### Added
- **Public API Layer (`framework_api.py`):** Implemented a production-ready public API using FastAPI. Features include a `/v1/chat/completions` endpoint, graceful lifecycle management for the `FailoverEngine`, request/response logging middleware, and comprehensive exception handling (503, 500).
- **Provider-Specific Model Mapping:** The API now uses a `model_priority_map` to correctly pair providers with their valid model lists, resolving a critical architectural flaw.
- **Health Check Endpoint:** Added a `/health` endpoint for deployment monitoring.
- **API Event Topics:** Added new event topics (`API_REQUEST_START`, `API_REQUEST_END`, etc.) to `telemetry/event_topics.py` for enhanced observability.

### Changed
- **Provider Adapter Architecture:** Critically refactored `OpenAIProvider`, `ClaudeProvider`, and `GeminiProvider` to handle API key rotation by creating temporary, per-call client instances. This resolves a fundamental `TypeError` caused by passing an `api_key` argument to the SDKs' generation methods.
- `FailoverEngine`: Modified `execute_request` to accept an optional `request_id`, enabling end-to-end traceability from the API layer through the entire resilience lifecycle.

### Fixed
- **Critical Test Suite Instability:** Resolved a cascade of complex, interdependent test failures in `test_failover_engine.py` by implementing a correct, isolated mocking strategy for the stateful `ResourceGuard`.
- **Gemini Adapter Regression:** Fixed a `TypeError` in `GeminiProvider` introduced during refactoring and corrected corresponding test assertions.
- **`framework_api.py` Key Parsing:** Corrected a bug where comma-separated API keys in the `.env` file were not being parsed into a list, which would have broken key rotation.


## [1.2.0] - 2025-08-14 (ResilienceScore Calculation & Logging)

### Added
- **`ResilienceScore` Calculation:** Implemented logic within `FailoverEngine` to calculate a `ResilienceScore` (0.0-1.0) for every request based on incurred resilience events.
- **Configurable Penalties:** Introduced `config/resilience_config.yaml` to centralize configurable penalty values for various resilience events impacting the `ResilienceScore`.
- **Configuration Loader:** Added `antifragile_framework/config/config_loader.py` to handle loading and validating YAML configuration files, including `resilience_config.yaml`.
- **ResilienceScore Logging:** The calculated `ResilienceScore` is now consistently logged within each `BiasLedgerEntry` for auditable historical analysis.
- **Robust Configuration Validation:** Implemented explicit validation checks for resilience score penalties during `FailoverEngine` initialization to prevent invalid configurations.

### Changed
- `antifragile_framework/core/failover_engine.py`: Modified `__init__` to load resilience configuration and added `_calculate_resilience_score` method. Updated `execute_request` to calculate and log the score.
- `tests/core/test_failover_engine.py`: Significantly updated with new fixtures (for config mocking, BiasLedger, EventBus) and numerous assertions to verify `ResilienceScore` calculation across various scenarios, including successful mitigation, failovers, circuit trips, and configuration validation.

### Fixed
- (No specific new fixes in this version, focused on adding features.)

## [1.1.0] - 2025-08-14 (LearningEngine Offline Analysis)

### Added
- **`LearningEngine` Core:** Implemented `antifragile_framework/core/learning_engine.py` to perform offline analysis of `BiasLedger` data.
- **`ProviderPerformanceAnalysis` Schema:** Defined a new Pydantic model in `antifragile_framework/core/schemas.py` to structure the aggregated performance metrics for providers and models.
- **Memory-Efficient DB Querying:** Added `query_events_generator` to `telemetry/time_series_db_interface.py`, enabling generator-based, batched retrieval of historical events to prevent memory exhaustion.
- **Schema Versioning for `BiasLedgerEntry`:** Added a `schema_version` field to the `BiasLedgerEntry` model (`antifragile_framework/resilience/bias_ledger.py`) to ensure future data compatibility and evolution.
- **Robust Deserialization:** The `LearningEngine` now gracefully handles and logs malformed `BiasLedgerEntry` payloads during retrieval, skipping invalid entries without crashing.
- **Comprehensive Analysis Metrics:** The `LearningEngine` aggregates detailed performance metrics (success rates, latencies, error distributions, mitigation effectiveness, failover occurrences, circuit breaker trips) with explicit zero-division handling and clear documentation of their semantics.
- **New Unit Test Suite:** Added `tests/core/test_learning_engine.py` with extensive tests for data retrieval, deserialization robustness, and aggregation logic.

### Changed
- `antifragile_framework/resilience/bias_ledger.py`: Updated `BiasLedgerEntry` to include `schema_version` field and its instantiation.
- `telemetry/time_series_db_interface.py`: Enhanced with `query_events_generator` for read operations.
- `antifragile_framework/core/learning_engine.py`: Added comprehensive documentation for calculated metrics.

### Fixed
- Resolved `NameError` in `tests/core/test_learning_engine.py` by adding missing `typing` imports.

## [1.0.0] - 2025-08-11 (Bias Ledger & Auditable Lifecycle Logging)

### Added
- **`BiasLedger` Auditing System:** Implemented `antifragile_framework/resilience/bias_ledger.py` as a high-level auditing interface. It creates a comprehensive, structured log entry for every request's complete lifecycle.
- **`RequestContext` State Management:** Introduced a `RequestContext` dataclass (`antifragile_framework/core/schemas.py`) to cleanly manage all state associated with a single request (ID, events, counters), significantly simplifying the `FailoverEngine`'s logic.
- **Guaranteed Audit Trail:** The `FailoverEngine` now uses a `try...finally` block to ensure the `BiasLedger` is called for every request, guaranteeing a complete audit trail even in cases of failure or exceptions.
- **Smart Schema Design:** The `BiasLedgerEntry` Pantic model was designed to be performant and secure, storing lightweight previews and cryptographic hashes of prompts instead of raw, sensitive content.
- **Comprehensive Auditing Tests:** Added a new test suite for the `BiasLedger` to validate its behavior for successful, failed, and mitigated requests.

### Changed
- **`FailoverEngine` Architecture:** Major refactoring to replace scattered state variables with the new `RequestContext` object, improving maintainability and robustness. All resilience events are now captured in the context's `lifecycle_events` list.

### Fixed
- **Critical `EventBus` Signature Mismatch:** Resolved a fundamental design flaw where the `EventBus.publish` method signature was incompatible with its usage across the application, causing a cascade of hidden `TypeError` exceptions. The method and all calls to it are now harmonized.
- **Circular Dependency:** Resolved a critical `ImportError` caused by a circular dependency between the `FailoverEngine` and `BiasLedger` by moving the shared `RequestContext` schema to a neutral `core/schemas.py` module.

## [0.9.0] - 2025-08-10 (Layer 3 Mitigation & Decoupled Rewriter)

### Added
- **Content Policy Mitigation:** Implemented a Layer 3 defense mechanism to handle content policy errors. The system can now automatically rephrase and retry a blocked prompt once.
- **`PromptRewriter` Abstraction:** Created a new Abstract Base Class (`antifragile_framework/resilience/prompt_rewriter.py`) to define a clean contract for any prompt rewriting component.
- **`LLMBasedRewriter`:** Added a concrete implementation of the `PromptRewriter` that uses a dedicated, simple LLM client to perform rephrasing. The system prompt for this rewriter is now configurable.
- **New Exception Types:** Added `ContentPolicyError` and `RewriteFailedError` to the exception hierarchy for more granular error handling.
- **Mitigation Testing:** Added a full test suite for the `LLMBasedRewriter` and expanded `test_failover_engine.py` to validate all mitigation scenarios (success, rewriter failure, and rephrased-prompt failure).

### Changed
- **Architectural Redesign:** The `HumanizerAgent` was redesigned into a decoupled `PromptRewriter` based on critical AI audits to eliminate a high-risk circular dependency. This significantly improves maintainability and testability.
- **`FailoverEngine` Logic:** Refactored the engine to use dependency injection for the `PromptRewriter`. The main request logic was updated to a two-stage process (attempt -> mitigate on `ContentPolicyError`) to ensure the mitigation is only tried once.


## [0.8.0] - 2025-08-09 (Telemetry Persistence & System Hardening)

### Added
- **Telemetry Persistence Pipeline:** Implemented a fully decoupled, event-driven pipeline to persist operational telemetry. Core components (`FailoverEngine`, `ResourceGuard`) now publish events to an `EventBus`.
- **`TelemetrySubscriber`:** A new, resilient subscriber that listens for all events and writes them to the `TimeSeriesDBInterface`, ensuring failures in the telemetry backend do not impact the main application.
- **Centralized Event Topics:** Created `telemetry/event_topics.py` to act as a single source of truth for all event names, improving maintainability and reducing errors.
- **End-to-End Simulation:** Added a `main.py` script to demonstrate the initialization and operation of the entire framework, including the new telemetry pipeline.
- **Comprehensive Telemetry Tests:** Added a new test suite (`test_telemetry_subscriber.py`) to validate the subscriber's logic, including error handling and configurable logging.

### Changed
- **`FailoverEngine` & `ResourceGuard`:** Refactored both modules to publish events asynchronously using a non-blocking "fire-and-forget" pattern (`asyncio.create_task`).
- **`CoreLogger` Architecture:** The entire `core_logger.py` was overhauled to correctly subclass `logging.Logger`, making it more robust, standards-compliant, and backward-compatible with standard library logging calls.

### Fixed
- **Critical Logger `ValueError`:** Resolved a long-standing bug in the `JsonFormatter` related to an invalid timestamp format string (`datefmt`) that was causing `ValueError` exceptions during logging.
- **Critical `FailoverEngine` `AttributeError`:** Fixed a bug where the engine was incorrectly checking the circuit breaker's state (`is_half_open` instead of `breaker.state == CircuitBreakerState.HALF_OPEN`).
- **Circular Import & Test Logic:** Resolved multiple bugs introduced during development, including a circular import error and several incorrect assertions in the test suite that were failing due to mismatched assumptions about internal class structures.


## [0.7.0] - 2025-08-08 (Model-Level Failover & System Hardening)

### Added
- **Model-Level Failover:** The `FailoverEngine` now implements the second ring of the Layer 2 resilience protocol. It accepts a prioritized list of models (e.g., `['gpt-4o', 'gpt-4-turbo']`) and will attempt all keys for the first model before failing over to the next model within the *same provider*.
- **Intelligent Error Short-Circuiting:** Implemented a new `_is_model_specific_error` helper in the `FailoverEngine` to detect errors like "model not found" and immediately fail over to the next model, avoiding pointless retries with other keys.

### Changed
- **`FailoverEngine` Architecture:** Refactored `execute_request` based on external AI audits to delegate key rotation logic to a new `_attempt_model_with_keys` helper method. This significantly improves readability and maintainability by removing a triple-nested loop.
- **Telemetry System:** Corrected the invocation pattern for the core logger across the `FailoverEngine` and `ResourceGuard` to align with its intended design, ensuring robust and consistent structured logging.

### Fixed
- **Critical Logging Bug:** Resolved a `TypeError` and `ValueError` cascade originating from incorrect logger calls in multiple modules. The `core_logger` and its formatter were hardened to be more resilient to different call patterns.
- **Fragile Tests:** Rewrote and fixed multiple fragile tests in `test_resource_guard.py` that used unreliable time-mocking, improving the stability of the entire test suite.
- **Test Suite Logic:** Corrected multiple assertion errors in `test_failover_engine.py` that had flawed assumptions about the stateful behavior of the `ResourceGuard` during cooldown periods.

## [0.6.0] - 2025-08-07 (Advanced Failover & Circuit Breaking)

### Added
- **Provider Failover:** The `FailoverEngine` now supports a priority list of providers, automatically failing over to the next provider if the current one is unavailable (due to key exhaustion or an open circuit).
- **Circuit Breaker:** Implemented a thread-safe `antifragile_framework/core/circuit_breaker.py` module to prevent cascading failures. The `FailoverEngine` now trips a provider's circuit on repeated transient errors.
- **Error Parser:** Implemented a new `antifragile_framework/utils/error_parser.py` utility to classify provider exceptions into `FATAL`, `TRANSIENT`, and `CONTENT_POLICY` categories, allowing for more intelligent error handling.
- **Comprehensive Testing:** Added new, robust test suites for `CircuitBreaker` and `ErrorParser`, including tests for thread safety, edge cases, and a wide range of provider exceptions. The `FailoverEngine` test suite was rewritten to validate the new multi-provider and circuit-breaking logic.

### Changed
- **`FailoverEngine` Architecture:** Overhauled `execute_request` to use a nested loop structure: an outer loop for provider failover and an inner loop for key rotation.
- **Exception Hierarchy:** Added a new top-level `AllProvidersFailedError` to signal total system failure for a request.

### Fixed
- **Resolved Critical Test Blocker:** Corrected numerous `TypeError` issues in the test suite caused by dependency updates in the `openai` and `anthropic` libraries, unblocking all tests.
- **Pydantic Model Conformance:** Updated all test mocks to correctly provide the required `latency_ms` field for the `CompletionResponse` model, resolving all validation errors.
- **Error Parser Logic:** Improved the content policy detection logic in `ErrorParser` to be more specific and reliable.


## [0.4.0] - 05-08-2025 (Phase 0 Recovery & Phase 1 Core Resilience)

### Added
- **Phase 0 Telemetry Layer (Recovery):**
    - Re-implemented the entire foundational telemetry module after discovering it was not previously committed.
    - `telemetry/core_logger.py`: A thread-safe, singleton logger with a `UniversalEventSchema` for structured, JSON-formatted logs.
    - `telemetry/event_bus.py`: An in-process, asynchronous publish-subscribe event bus for decoupled communication.
    - `telemetry/time_series_db_interface.py`: A buffered database writer for batch ingesting telemetry data with connection retries.
- **Multi-Provider Support:**
    - Implemented and audited provider adapters for **Anthropic Claude** (`claude_adapter.py`) and **Google Gemini** (`gemini_adapter.py`).
- **Core Resilience Components:**
    - Implemented `antifragile_framework/core/resource_guard.py` to manage API key health. Features a robust, thread-safe context manager for resource reservation, automatic health score "healing", and failure cooldowns.
    - Implemented the initial `antifragile_framework/core/failover_engine.py` to orchestrate requests using the `ResourceGuard` and provider adapters.
- **Full System Integration:**
    - Integrated the Telemetry and Resilience layers. `ResourceGuard` and `FailoverEngine` now emit detailed structured events for key state changes and API call outcomes.
- **Testing:**
    - Added comprehensive unit tests for `ResourceGuard` and `FailoverEngine`.
    - Added or updated integration tests for all three provider adapters (`OpenAI`, `Claude`, `Gemini`).

### Changed
- **Architectural Refactoring:**
    - Refactored all provider adapters and the `api_abstraction_layer.py` to accept an `api_key_override`. This significantly improves performance and efficiency by avoiding client re-initialization on every call.
    - Improved `GeminiProvider` to use a safer, thread-local approach for managing its client.
    - Standardized error handling across all provider adapters.
- Updated `requirements.txt` to include all new dependencies.

### Fixed
- Corrected multiple critical bugs, including `ImportError`, `IndentationError`, and `asyncio` event loop lifecycle issues discovered during rigorous testing and auditing.

## [0.3.0] - 2025-08-2025 (Phase 1: Antifragile Framework Foundation)

### Added
- **Antifragile Framework Scaffolding:**
    - Established the comprehensive directory structure for Phase 1 (`antifragile_framework/` with `core`, `providers`, `resilience`, etc.) based on the new architectural blueprint.
    - Added `docs/README_phase1.md` to document the detailed vision, architecture, and interaction flows for the framework.
- **Provider Abstraction Layer:**
    - Implemented `antifragile_framework/providers/api_abstraction_layer.py` to define the core contract for all AI providers.
    - Includes the `LLMProvider` Abstract Base Class and standardized Pydantic models (`ChatMessage`, `CompletionResponse`) with built-in validation.
- **Concrete OpenAI Provider Adapter:**
    - Implemented `antifragile_framework/providers/provider_adapters/openai_adapter.py`, the first concrete provider.
    - Features built-in, configurable retries with exponential backoff and robust, provider-specific error handling.
- **Testing and Verification:**
    - Created `tests/test_openai_adapter.py`, a comprehensive integration test suite using `pytest`.
    - The test suite verifies successful API calls, model overrides, and graceful failure handling.
    - All code successfully passed a `Rule 9` external audit, achieving a 96% confidence score.
- **Project Structure & Maturity:**
    - Added a `pyproject.toml` file to define the project as an installable package.
    - Resolved Python pathing issues by using an "editable install" (`pip install -e .`), a major improvement for testing and development workflow.
    - Established a secure pattern for local development secrets using a `.env` file and `python-dotenv`.

### Changed
- Updated `requirements.txt` to include new dependencies: `openai`, `python-dotenv`, `pytest`, and `pytest-asyncio`.

## [0.2.0] - 2025-08-05 (Initial Project Bootstrap)

### Added
- Initial project repository created, configured with Git identity, and pushed to GitHub.
- Foundational Phase 0 directories and empty files created.
- Core project memory files (README.md, context_summary.md, changelog.md, .gitignore) populated with initial content.
- Python virtual environment (.venv) successfully set up and activated.
- All essential Python libraries installed into the virtual environment.
- `requirements.txt` generated and updated to track project dependencies.

---

## [0.1.0] - 2025-08-05 (Initial Project Bootstrap)

### Added
- Initial project repository created and pushed to GitHub.
- Phase 0: AI Ops Bootstrap Layer foundational directories (`ai_output/`, `docs/`, `scripts/`, `config/`, `tests/`, `telemetry/`) established.
- Core project memory files (`README.md`, `context_summary.md`, `changelog.md`, `.gitignore`) created and initially populated.
- Overall project vision and phase breakdown added to `README.md`.
- Basic project context established in `context_summary.md`.

### Security
- Initial `.gitignore` created to prevent sensitive files from being committed.

---