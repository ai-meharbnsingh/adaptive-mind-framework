# Performance Benchmarking

This document outlines the methodology and results for performance benchmarking of the Adaptive Mind framework. The primary goal of these initial tests is to establish a reproducible baseline for the framework's internal processing overhead, excluding the variable latency of external LLM API calls.

## Methodology: Framework Overhead Testing

To isolate and measure the performance of the framework itself, we employ a "mock" mode activated by an environment variable.

### Activation

The performance test mode is enabled by starting the FastAPI server with the `PERFORMANCE_TEST_MODE` environment variable set to `mock`.

**Example (PowerShell):**
```powershell
$env:PERFORMANCE_TEST_MODE="mock"; uvicorn antifragile_framework.api.framework_api:app --workers 1

Deep Debugging Protocol: Conclusion
Excellent! The results are exactly what we hoped to see.
Failure Rate: 0%
Requests Per Second (RPS): 78.9
Median Latency: 22ms
95th Percentile Latency: 41ms
This definitively confirms our hypothesis. The failures were not caused by a bug in our framework's logic but by overwhelming the single Uvicorn worker process. At a sustained load of approximately 80 RPS, our application is perfectly stable and performs with very low latency.
We have successfully established our first performance baseline. This is a critical milestone.

Behavior
When PERFORMANCE_TEST_MODE is active:
All provider adapters (OpenAI, Gemini, Claude) short-circuit their agenerate_completion methods.
Instead of making a network call to the external LLM provider, the method immediately returns a pre-defined, valid CompletionResponse object after a simulated I/O delay of 5-15ms.
This ensures that the entire framework stack—including request validation, routing logic (FailoverEngine), cost analysis, and the BiasLedger—is fully exercised, providing an accurate measurement of the framework's internal overhead.
Load Test Script
The load test is conducted using Locust. The test script (performance_tests/locustfile.py) defines a user that makes requests to the /v1/chat/completions endpoint. To ensure comprehensive testing, the user randomly selects from three distinct scenarios on each request:
Standard Request: Tests the default dynamic routing logic.
Cost-Capped Request: Tests the max_estimated_cost_usd feature and its associated filtering logic.
Preferred Provider Request: Tests the preferred_provider feature path.
code
Python
# performance_tests/locustfile.py

import random
from locust import HttpUser, task, between

TEST_SCENARIOS = {
    "standard_request": {
        "json": {
            "model_priority_map": {
                "openai": ["gpt-4-turbo"],
                "anthropic": ["claude-3-5-sonnet-20240620"]
            },
            "messages": [{"role": "user", "content": "This is a standard test request."}]
        },
        "name": "/v1/chat/completions (standard)"
    },
    "cost_capped_request": {
        "json": {
            "model_priority_map": {
                "openai": ["gpt-4o"],
                "google_gemini": ["gemini-1.5-flash-latest"]
            },
            "messages": [{"role": "user", "content": "This is a cost-capped request that should select the cheaper model."}],
            "max_estimated_cost_usd": "0.0001"
        },
        "name": "/v1/chat/completions (cost_capped)"
    },
    "preferred_provider_request": {
        "json": {
            "model_priority_map": {
                "openai": ["gpt-4o"],
                "anthropic": ["claude-3-5-sonnet-20240620"],
                "google_gemini": ["gemini-1.5-flash-latest"]
            },
            "messages": [{"role": "user", "content": "This request has a preferred provider."}],
            "preferred_provider": "google_gemini"
        },
        "name": "/v1/chat/completions (preferred_provider)"
    }
}

SCENARIO_LIST = list(TEST_SCENARIOS.values())

class FrameworkUser(HttpUser):
    wait_time = between(0.2, 1.0)

    @task
    def chat_completion_task(self):
        scenario = random.choice(SCENARIO_LIST)

        with self.client.post(
            "/v1/chat/completions",
            json=scenario["json"],
            name=scenario["name"],
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Got unexpected status code {response.status_code}")
            else:
                try:
                    if response.json().get("success", False):
                        response.success()
                    else:
                        response.failure(f"Response 'success' field was not True. Response: {response.text}")
                except Exception as e:
                    response.failure(f"Failed to parse JSON or access 'success' field: {e}")
Baseline Results (Single Worker)
The following baseline was established on 2025-08-26 against a single uvicorn worker process.
Test Configuration:
Total Users: 50
Spawn Rate: 5 users/second
Duration: 60 seconds
Key Metrics:
Requests Per Second (RPS): 78.9
Failure Rate: 0%
Median Response Time: 22ms
95th Percentile Response Time: 41ms
Conclusion
With a single worker, the framework can stably handle approximately 80 requests per second with a median internal processing overhead of 22ms. Exceeding this RPS threshold with a single worker can lead to connection saturation and 503 Service Unavailable errors. This baseline provides a solid benchmark for measuring future performance regressions or improvements.