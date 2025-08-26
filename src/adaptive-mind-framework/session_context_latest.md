🧠 CONTEXT:
# ✨ Project Context for Adaptive Mind

## 📄 Core Project Files
### context_summary.md:
```markdown
# 🧠 Project Context Summary (Last Updated: 2025-08-25 UTC)

## 🎯 Current Goal:
Continue with "Day 22-28: Phase 1 Final Integration," focusing on performance testing and documentation.

## 📈 Recent Progress:
- **Initial Security Hardening Complete:** Successfully performed the initial security audit of the framework.
- **Tools Installed:** Installed and configured `bandit` (for static code analysis) and `safety` (for dependency scanning).
- **Dependency Scan Passed:** The `safety` scan confirmed that the project has **zero** known vulnerabilities in its third-party dependencies.
- **Static Code Analysis Passed:** The `bandit` scan confirmed that the `antifragile_framework` codebase has **zero** medium or high-severity security issues, passing its initial code-level security review.

## 🚧 Current Challenges/Blockers:
- **None.** The framework is functionally stable, E2E tested, and has passed its initial security audit.

##▶️ Next Steps & Immediate Focus:
- **Performance Benchmarking:** Begin drafting the initial performance and load testing suite with **Locust** to establish baseline metrics for Requests Per Second (RPS) and latency.
- **Documentation:** Start creating the initial user-facing commercial documentation for the framework.

## 🔗 Relevant Code Changes (Since Last Summary):
- `requirements.txt` (**updated** with security tools `bandit` and `safety`)
```
### changelog.md (Last few entries):
```markdown
# 📜 Changelog - Adaptive Mind Project

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


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
... (truncated for brevity)
```
## 📚 Phase 1 Documentation (README_phase1.md):
```markdown
# Part I: Antifragile Resilience Framework (The "Adaptive Mind")

> [SECTION THEME: CORE RESILIENCE & ADAPTATION - EXTERNALLY LICENSABLE]

The "Adaptive Mind" operates as a four-layer defense-in-depth strategy, meticulously designed to not just survive but learn and thrive from system stresses. An error must penetrate all four layers before the system halts. This framework is robust, transparent, and designed for commercial licensing.

---

## 1. Project Structure

antifragile_framework/
├── api/
│ ├── framework_api.py # RESTful API for integration
│ └── webhooks.py # Event-driven notifications
├── core/
│ ├── health_monitor.py # Real-time provider health scoring
│ ├── resource_guard.py # Tracks and maintains health scores for keys/providers
│ ├── failover_engine.py # Intelligent provider switching (Key, Model, Provider rings)
│ ├── circuit_breaker.py # Prevent cascading failures (with Exponential Backoff)
│ ├── learning_engine.py # Pattern recognition & optimization (ML-based prediction, online/offline learning)
│ └── humanizer_agent.py # Rephrases prompts for content policy issues
├── providers/
│ ├── api_abstraction_layer.py # Standardized interface for external AI providers
│ ├── provider_registry.py # Dynamic provider management
│ └── provider_adapters/ # Standardized API interfaces for specific providers
│ ├── openai_adapter.py
│ ├── gemini_adapter.py
│ ├── claude_adapter.py
│ └── custom_adapter.py
├── resilience/
│ ├── key_ring_manager.py # API key rotation & management
│ ├── cost_optimizer.py # Real-time cost-quality optimization
│ ├── sanitizer.py # Cross-provider data sanitization
│ └── bias_ledger.py # Transparency & audit logging (leverages comprehensive logging)
├── utils/
│ └── error_parser.py # Classifies root cause of failures
└── config/
├── resilience_config.yaml # Framework configuration (including Resilience Score penalties) # CONFIRM THIS LINE IS PRESENT
├── provider_profiles.json # Provider-specific settings
└── emergency_role_map.json # "Last Resource Standing" protocol definitions


---

## 2. Interaction Flow

-   -   **Primary Request Flow (Data Flow):**
    `External Application → framework_api.py (accepts optional 'preferred_provider') → failover_engine.py (dual-mode logic) → api_abstraction_layer.py → provider_adapters → External AI Provider`

-   **Health & Performance Feedback Loop:**
    `External AI Provider (response/failure) → provider_adapters → resource_guard.py / health_monitor.py (updates health scores) → failover_engine.py (informs selection)`
    *(All interactions are logged by the comprehensive logging system as "Provider Performance Data" and "Circuit Breaker & Health Monitoring.")*

-   **Learning & Optimization Feedback Loop:**
    `bias_ledger.py (failure data, resilience scores) → learning_engine.py (pattern analysis) → failover_engine.py (parameter tuning)`
    *(All learning inputs are logged as "Failover & Recovery Events" and "Learning & Adaptation Data.")*

-   **Error Handling Flow:**
    `failover_engine.py (on exception) → error_parser.py (classify) → Specific mitigation (e.g., humanizer_agent.py) / circuit_breaker.py / Layer 2-4 failover`
    *(All error handling paths are meticulously logged.)*

---

## 3. The Four Layers of Defense

### Layer 1: The Pre-emptive Health Audit & Performance-Based Selection
- **Mechanism:** Powered by `resource_guard.py`, the system calculates and maintains a numerical **Health Score (0.0 to 1.0)** for every API key, which intelligently "heals" over time.
- **Function:** Before any API call, the `failover_engine.py` selects the key with the highest available health score, preemptively using its most reliable resource.

### Layer 2: The Intelligent Failover Protocol (Key, Model, & Provider Rings)
- **Mechanism:** A sophisticated, multi-stage failover within the `failover_engine.py`. Every failover event is logged as a "Failover & Recovery Event".
- **Function:** Upon failure, the system automatically cycles through (1) the next healthiest **Key**, (2) the next **Model** in the chain, and finally (3) the next **Provider**.

### Layer 3: Intelligent Error-Cause Mitigation & The Circuit Breaker
- **Mechanism:** The system uses `utils/error_parser.py` to classify the root cause of failures and react with nuance. Mitigation actions feed "Learning & Adaptation Data".
- **Function:**
    - **Quota Errors (429):** Trigger immediate key failover and penalize the key's Health Score.
    - **Content Filter Errors (400/403):** Trigger the "Humanization Fallback," where `humanizer_agent.py` rephrases the prompt for one retry.
    - **Persistent Failures:** The `circuit_breaker.py` with Exponential Backoff protects the system from hammering a failing service.

### Layer 4: The Ultimate Fallback ("Last Resource Standing" Protocol)
- **Mechanism:** The system's final safety net, defined in `config/emergency_role_map.json`. Usage is logged as a critical "Failover & Recovery Event".
- **Function:** When an entire agent role becomes unrecoverable, the orchestrator re-tasks the job to any other healthy agent, regardless of its original role.

---

## 4. The Bias Ledger & Resilience Score: Quantifying Performance

The "Adaptive Mind" does not just survive failure; it meticulously records and quantifies it.

- **The Bias Ledger:** For every task, a final, consolidated log is written to the comprehensive data store. This structured report contains a full, tamper-proof audit of all resilience events, fallbacks, and re-tasking. It serves as the central repository for "Provider Performance DNA," "Decision Context," and "Learning Patterns."

- **The Resilience Score:** The crown jewel of the framework. Every task is assigned a final **Resilience Score**, starting at 1.0 and penalized for every resilience event (defined in `config/resilience_config.yaml`). A score of 1.0 indicates a flawless execution, while a lower score provides an immediate, quantifiable measure of the stress the system endured.
```

📦 GITHUB:
https://github.com/ai-meharbnsingh/adaptive-mind/tree/feature/phase1-final-integration
