# debug_mock_issue.py
import asyncio
from unittest.mock import Mock, MagicMock
from contextlib import contextmanager


# This simulates the NoResourcesAvailableError from our framework
class NoResourcesAvailableError(Exception):
    pass


# --- Simplified Flawed Mock ---
# This recreates the flawed, stateful logic from our test fixture.
def create_flawed_mock_guard():
    api_keys = ["key-1", "key-2"]
    mock_guard = MagicMock()

    @contextmanager
    def _mock_resource_context(key_id):
        print(f"    [Guard] Providing resource: {key_id}")
        yield key_id

    # The flaw: a single iterator is created and shared.
    side_effects_iterator = iter([
        _mock_resource_context(api_keys[0]),
        _mock_resource_context(api_keys[1]),
        NoResourcesAvailableError("No more keys")
    ])

    mock_guard.get_resource = Mock(side_effect=side_effects_iterator)
    return mock_guard


# --- Simplified Engine Logic ---
# This mimics the nested loops of the FailoverEngine.
async def run_failover_simulation(guard):
    models = ["model-A", "model-B"]

    for model in models:
        print(f"\n[Engine] Starting attempts for {model}")
        try:
            # Inner loop: try all keys for the current model
            while True:
                print(f"  [Engine] Requesting a key for {model}...")
                with guard.get_resource() as resource:
                    print(f"  [Engine] Got key '{resource}'. Simulating failure...")
            # This loop is expected to break with NoResourcesAvailableError
        except NoResourcesAvailableError:
            print(f"  [Engine] Exhausted all keys for {model}. Failing over to next model.")
            continue  # Move to the next model

    print("\n[Engine] Simulation finished.")


# --- Execution ---
async def main():
    print("--- RUNNING DEBUG SCRIPT WITH FLAWED MOCK ---")
    flawed_guard = create_flawed_mock_guard()
    try:
        await run_failover_simulation(flawed_guard)
    except Exception as e:
        print(f"\n--- !!! SIMULATION CRASHED !!! ---")
        print(f"Error Type: {type(e).__name__}")
        print("This happens because the iterator was exhausted and not reset for model-B.")


if __name__ == "__main__":
    asyncio.run(main())