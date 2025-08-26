# performance_tests/locustfile.py

import random
from locust import HttpUser, task, between

# As per expert feedback, define multiple test scenarios to exercise different
# code paths within the framework. This provides a more comprehensive baseline.
TEST_SCENARIOS = {
    # A standard request that will use the default dynamic routing logic.
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
    # A request with a tight cost cap, forcing the cost-capping logic to be evaluated.
    "cost_capped_request": {
        "json": {
            "model_priority_map": {
                "openai": ["gpt-4o"],                      # Higher cost model
                "google_gemini": ["gemini-1.5-flash-latest"] # Lower cost model
            },
            "messages": [{"role": "user", "content": "This is a cost-capped request that should select the cheaper model."}],
            "max_estimated_cost_usd": "0.0001" # A very low cap to ensure this logic path is tested.
        },
        "name": "/v1/chat/completions (cost_capped)"
    },
    # A request where the user specifies a preferred provider, testing another key feature.
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

# Convert the dictionary to a list of scenarios for random.choice
SCENARIO_LIST = list(TEST_SCENARIOS.values())


class FrameworkUser(HttpUser):
    """
    Simulates a user making various API calls to the antifragile framework.
    """
    # Users will wait between 0.2 and 1.0 seconds between tasks.
    # This is a shorter wait time because our mocked responses will be very fast.
    wait_time = between(0.2, 1.0)

    @task
    def chat_completion_task(self):
        """
        Picks a random scenario and sends it to the chat completions endpoint.
        """
        # Pick a random scenario for each task execution
        scenario = random.choice(SCENARIO_LIST)

        with self.client.post(
            "/v1/chat/completions",
            json=scenario["json"],
            name=scenario["name"],  # Group stats by scenario name in Locust UI
            catch_response=True     # Allows us to check the response manually
        ) as response:
            # Check for a successful HTTP status code
            if response.status_code != 200:
                response.failure(f"Got unexpected status code {response.status_code}")
            else:
                try:
                    # Check that the business logic also reported success
                    if response.json().get("success", False):
                        response.success()
                    else:
                        response.failure(f"Response 'success' field was not True. Response: {response.text}")
                except Exception as e:
                    response.failure(f"Failed to parse JSON or access 'success' field: {e}")