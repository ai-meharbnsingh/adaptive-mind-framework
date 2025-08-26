# main.py

import os
import asyncio
import logging
from dotenv import load_dotenv

from antifragile_framework.core.failover_engine import FailoverEngine
from antifragile_framework.core.exceptions import AllProvidersFailedError
from antifragile_framework.providers.api_abstraction_layer import ChatMessage
from telemetry.event_bus import EventBus
from telemetry.time_series_db_interface import TimeSeriesDBInterface
from telemetry.telemetry_subscriber import TelemetrySubscriber
from telemetry.core_logger import core_logger

# Configure basic logging for the application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()


def setup_provider_configs():
    """
    Loads provider configurations from environment variables.
    This is a placeholder for a more robust configuration system (e.g., YAML file).
    """
    return {
        "openai": {
            "api_keys": [
                os.getenv("OPENAI_API_KEY_1"),
                os.getenv("OPENAI_API_KEY_2_INVALID"),  # An invalid key to test failover
                os.getenv("OPENAI_API_KEY_3")
            ],
            "resource_config": {"cooldown": 10},  # Short cooldown for demo
            "circuit_breaker_config": {"failure_threshold": 2, "recovery_timeout": 20}
        },
        "google_gemini": {
            "api_keys": [
                os.getenv("GEMINI_API_KEY_1")
            ],
            "resource_config": {"cooldown": 10},
            "circuit_breaker_config": {"failure_threshold": 2, "recovery_timeout": 20}
        }
        # Anthropic is skipped as per project context
    }


async def run_simulation():
    """
    Sets up the Antifragile Framework and runs a test simulation.
    """
    core_logger.info("--- Starting Antifragile Framework Simulation ---")

    # 1. Initialize Telemetry Infrastructure
    core_logger.info("Initializing telemetry system...")
    event_bus = EventBus()
    db_interface = TimeSeriesDBInterface(db_name="adaptive_mind_telemetry", buffer_size=5, flush_interval=5)

    # The subscriber listens to the bus and writes to the DB
    subscriber = TelemetrySubscriber(event_bus, db_interface)
    subscriber.subscribe_to_all_events()  # Activate the subscriber
    core_logger.info("Telemetry system initialized and subscriber is active.")

    # 2. Initialize Core Resilience Framework
    core_logger.info("Initializing Failover Engine...")
    provider_configs = setup_provider_configs()
    failover_engine = FailoverEngine(provider_configs, event_bus=event_bus)
    core_logger.info("Failover Engine initialized.")

    # 3. Define the workload
    messages = [ChatMessage(role="user", content="Tell me a very short story about a resilient robot.")]
    # This model does not exist, forcing a model failover
    models = ["gpt-4o-nonexistent", "gpt-4o"]
    provider_priority = ["openai", "google_gemini"]

    # 4. Execute the request
    core_logger.info(f"Executing request with provider priority: {provider_priority} and models: {models}")
    try:
        response = await failover_engine.execute_request(
            provider_priority=provider_priority,
            models=models,
            messages=messages,
            max_tokens=50
        )
        core_logger.info(f"--- Simulation SUCCESS ---")
        core_logger.info(f"Final Response from: {response.provider_name}/{response.model}")
        core_logger.info(f"Content: {response.content}")

    except AllProvidersFailedError as e:
        core_logger.error(f"--- Simulation FAILED: All providers were exhausted. ---")
        core_logger.error(f"Error details: {e}")

    finally:
        # 5. Graceful shutdown
        core_logger.info("Shutting down telemetry database interface...")
        await db_interface.shutdown()
        core_logger.info("--- Simulation Complete ---")


if __name__ == "__main__":
    # To see the non-blocking nature, we can run another task concurrently
    async def background_task():
        count = 0
        while True:
            # This task will run alongside the main simulation, proving the event
            # publishing is non-blocking.
            print(f"Background task running... ({count})")
            count += 1
            await asyncio.sleep(2)


    # In a real app, you'd have a proper event loop manager.
    # Here, we just run the simulation.
    loop = asyncio.get_event_loop()
    # main_task = loop.create_task(run_simulation())
    # bg_task = loop.create_task(background_task())
    # loop.run_until_complete(main_task)
    # bg_task.cancel() # Clean up the background task
    # loop.close()

    # Simplified run for clarity
    asyncio.run(run_simulation())