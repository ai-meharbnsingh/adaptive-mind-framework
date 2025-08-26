# antifragile_framework/core/learning_engine.py

import sys
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

# Standardized path setup relative to the current file
# Assuming current file is in PROJECT_ROOT/01_Framework_Core/antifragile_framework/core/
from pathlib import Path
from typing import Any, Dict, Iterator, List

from pydantic import ValidationError

CURRENT_DIR = Path(__file__).parent
FRAMEWORK_ROOT = CURRENT_DIR.parent.parent  # Points to antifragile_framework/
TELEMETRY_PATH = (
    CURRENT_DIR.parent.parent.parent.parent / "telemetry"
)  # Points to 01_Framework_Core/telemetry/


sys.path.insert(0, str(FRAMEWORK_ROOT))
sys.path.insert(0, str(TELEMETRY_PATH))

# Import from standardized locations
try:
    from resilience.bias_ledger import BiasLedgerEntry
    from schemas import ProviderPerformanceAnalysis
    from telemetry import event_topics
    from telemetry.core_logger import UniversalEventSchema, core_logger
    from telemetry.time_series_db_interface import TimeSeriesDBInterface
except ImportError as e:
    logging.critical(
        f"CRITICAL ERROR: Failed to import core dependencies for LearningEngine: {e}. "
        f"LearningEngine will not function correctly.",
        exc_info=True,
    )

    # Define minimal mocks to prevent hard crashes
    class TimeSeriesDBInterface:
        def __init__(self, conn_manager):
            pass

        async def initialize(self):
            pass

        async def close(self):
            pass

        async def record_event(self, event_schema):
            pass

        async def query_events_generator(self, *args, **kwargs):
            for item in []:
                yield item

    class EventTopics:  # Mock selected topics
        API_CALL_FAILURE = "api.call.failure"
        ALL_PROVIDERS_FAILED = "all_providers.failed"
        BIAS_LOG_ENTRY_CREATED = "bias.log_entry.created"

    event_topics = EventTopics()

    class MockCoreLogger:
        def log(self, event):
            logging.info(f"MockCoreLogger: {event.get('event_type')}")

    core_logger = MockCoreLogger()

    class UniversalEventSchema:
        def __init__(self, **kwargs):
            pass

        def model_dump(self):
            return {}

    class BiasLedgerEntry:
        def __init__(self, **kwargs):
            pass

        def model_validate(cls, data):
            return BiasLedgerEntry()

    class ProviderPerformanceAnalysis:
        def __init__(self, **kwargs):
            pass


log = logging.getLogger(__name__)


class LearningEngine:
    """
    The LearningEngine processes historical data from the BiasLedger (via TimeSeriesDBInterface)
    to identify provider performance patterns and inform adaptive strategies.
    """

    def __init__(self, db_interface: TimeSeriesDBInterface):
        if not isinstance(db_interface, TimeSeriesDBInterface):
            raise TypeError(
                "db_interface must be an instance of TimeSeriesDBInterface"
            )
        self.db_interface = db_interface
        log.info("LearningEngine initialized.")

    async def get_raw_bias_ledger_entries(
        self,  # Changed to async for proper DB interaction
        start_time: datetime,
        end_time: datetime,
        batch_size: int = 1000,
    ) -> Iterator[Dict[str, Any]]:  # Yield raw dicts first
        """
        Retrieves raw BiasLedgerEntry events from the database within a given time range
        and attempts to deserialize them into BiasLedgerEntry Pydantic objects.
        Malformed entries are logged and skipped.

        Yields: UniversalEventSchema.model_dump() dictionaries from TimeSeriesDB.
        """
        log.info(
            f"Retrieving BiasLedger entries from {start_time} to {end_time}..."
        )

        # Use query_events_generator directly as it already yields the raw UniversalEventSchema payload (dict)
        # Note: BiasLedgerEntry is the payload of BIAS_LOG_ENTRY_CREATED event.
        async for (
            raw_event_dict
        ) in self.db_interface.query_events_generator(  # Use async for generator
            event_type=event_topics.BIAS_LOG_ENTRY_CREATED,
            start_time=start_time,
            end_time=end_time,
            batch_size=batch_size,
        ):
            # The raw_event_dict is a dict representation of UniversalEventSchema.model_dump()
            # Its 'payload' field is the actual BiasLedgerEntry data.
            yield raw_event_dict

    async def analyze_provider_performance(
        self, start_time: datetime, end_time: datetime  # Changed to async
    ) -> List[ProviderPerformanceAnalysis]:
        """
        Analyzes BiasLedger entries to aggregate performance metrics for each provider/model.
        """
        log.info(
            f"Analyzing provider performance from {start_time} to {end_time}..."
        )

        aggregated_data = defaultdict(
            lambda: defaultdict(
                lambda: {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "total_latency_ms": 0.0,
                    "error_distribution": defaultdict(int),
                    "mitigation_attempted_count": 0,
                    "mitigation_successful_count": 0,
                    "failover_occurred_count": 0,
                    "circuit_breaker_tripped_count": 0,
                    "resilience_scores_sum": 0.0,
                    "resilience_score_count": 0,
                }
            )
        )

        async for event_payload_dict in self.get_raw_bias_ledger_entries(
            start_time, end_time
        ):  # Await the generator
            try:
                # The payload of the telemetry event IS the BiasLedgerEntry data
                ledger_entry_data = event_payload_dict.get("payload", {})
                ledger_entry = BiasLedgerEntry.model_validate(
                    ledger_entry_data
                )

                # CORRECTED: Use the new, separate fields from the updated BiasLedgerEntry schema
                provider_name = ledger_entry.final_provider or "unknown"
                model_name = ledger_entry.final_model or "unknown"

                provider_model_metrics = aggregated_data[provider_name][
                    model_name
                ]
                provider_model_metrics["total_requests"] += 1

                if (
                    ledger_entry.outcome == "SUCCESS"
                    or ledger_entry.outcome == "MITIGATED_SUCCESS"
                ):
                    provider_model_metrics["successful_requests"] += 1
                    provider_model_metrics[
                        "total_latency_ms"
                    ] += ledger_entry.total_latency_ms
                else:
                    error_type = "unknown_failure"
                    if ledger_entry.resilience_events:
                        for event in reversed(
                            ledger_entry.resilience_events
                        ):  # Iterate through lifecycle events
                            event_type = event.get("event_type")
                            payload_inner = event.get("payload", {})
                            if (
                                event_type == event_topics.API_CALL_FAILURE
                                and payload_inner.get("error_type")
                            ):
                                error_type = payload_inner["error_type"]
                                break
                            elif (
                                event_type == event_topics.ALL_PROVIDERS_FAILED
                            ):
                                error_type = "all_providers_failed"
                                break
                    provider_model_metrics["error_distribution"][
                        error_type
                    ] += 1

                if ledger_entry.mitigation_attempted:
                    provider_model_metrics["mitigation_attempted_count"] += 1
                    if ledger_entry.mitigation_succeeded:
                        provider_model_metrics[
                            "mitigation_successful_count"
                        ] += 1

                for (
                    event
                ) in (
                    ledger_entry.resilience_events
                ):  # Iterate through lifecycle events
                    if event.get("event_type") in [
                        event_topics.PROVIDER_FAILOVER,
                        event_topics.MODEL_FAILOVER,
                        event_topics.API_KEY_ROTATION,
                    ]:
                        provider_model_metrics["failover_occurred_count"] += 1
                    elif (
                        event.get("event_type") == event_topics.CIRCUIT_TRIPPED
                    ):
                        provider_model_metrics[
                            "circuit_breaker_tripped_count"
                        ] += 1

                if ledger_entry.resilience_score is not None:
                    provider_model_metrics[
                        "resilience_scores_sum"
                    ] += ledger_entry.resilience_score
                    provider_model_metrics["resilience_score_count"] += 1

            except ValidationError as ve:
                log.warning(
                    f"Skipping malformed BiasLedgerEntry (ValidationError) from DB event. "
                    f"Event ID: {event_payload_dict.get('event_id', 'N/A')}. Error: {ve}"
                )
            except Exception as e:
                log.error(
                    f"Skipping malformed BiasLedgerEntry (General Error) from DB event. "
                    f"Event ID: {event_payload_dict.get('event_id', 'N/A')}. Error: {e}",
                    exc_info=True,
                )

        results: List[ProviderPerformanceAnalysis] = []

        for provider_name, models_data in aggregated_data.items():
            for model_name, metrics in models_data.items():
                total_requests = metrics["total_requests"]
                successful_requests = metrics["successful_requests"]
                mitigation_attempted = metrics["mitigation_attempted_count"]
                mitigation_successful = metrics["mitigation_successful_count"]

                success_rate = (
                    successful_requests / total_requests
                    if total_requests > 0
                    else 0.0
                )
                # Ensure successful_requests > 0 before division
                avg_latency_ms = (
                    metrics["total_latency_ms"] / successful_requests
                    if successful_requests > 0
                    else 0.0
                )
                mitigation_success_rate = (
                    mitigation_successful / mitigation_attempted
                    if mitigation_attempted > 0
                    else 0.0
                )
                failover_rate = (
                    metrics["failover_occurred_count"] / total_requests
                    if total_requests > 0
                    else 0.0
                )
                circuit_breaker_trip_rate = (
                    metrics["circuit_breaker_tripped_count"] / total_requests
                    if total_requests > 0
                    else 0.0
                )
                avg_resilience_score = (
                    metrics["resilience_scores_sum"]
                    / metrics["resilience_score_count"]
                    if metrics["resilience_score_count"] > 0
                    else 1.0
                )  # Default to 1.0 if no scores recorded

                results.append(
                    ProviderPerformanceAnalysis(
                        provider_name=provider_name,
                        model_name=model_name,
                        total_requests=total_requests,
                        successful_requests=successful_requests,
                        success_rate=success_rate,
                        avg_latency_ms=avg_latency_ms,
                        error_distribution=dict(metrics["error_distribution"]),
                        mitigation_attempted_count=mitigation_attempted,
                        mitigation_successful_count=mitigation_successful,
                        mitigation_success_rate=mitigation_success_rate,
                        failover_occurred_count=metrics[
                            "failover_occurred_count"
                        ],
                        failover_rate=failover_rate,
                        circuit_breaker_tripped_count=metrics[
                            "circuit_breaker_tripped_count"
                        ],
                        circuit_breaker_trip_rate=circuit_breaker_trip_rate,
                        avg_resilience_score=avg_resilience_score,
                        analysis_period_start=start_time,
                        analysis_period_end=end_time,
                    )
                )
        log.info(
            f"Provider performance analysis complete. Generated {len(results)} analysis objects."
        )
        return results


# Example Usage (for testing this module in isolation)
async def main():
    print("Starting LearningEngine demo...")

    # Mock Database
    class MockConnectionManager:
        async def get_connection(self):
            return None

        async def release_connection(self, conn):
            pass

        async def close_all_connections(self):
            pass

        async def fetch_rows(self, query, *args):
            return []

    class MockTimeSeriesDB(TimeSeriesDBInterface):
        def __init__(self, conn_manager):
            self.conn_manager = conn_manager

        async def initialize(self):
            pass

        async def close(self):
            pass

        async def record_event(self, event_schema):
            pass

        async def query_events(self, *args, **kwargs):
            return []

        async def aggregate_events(self, *args, **kwargs):
            return []

        # Simulate some BiasLedgerEntry events for testing LearningEngine
        async def query_events_generator(
            self, event_type, start_time, end_time, batch_size
        ):
            if event_type == event_topics.BIAS_LOG_ENTRY_CREATED:
                for i in range(15):  # Generate 15 mock events
                    provider = "openai" if i % 2 == 0 else "anthropic"
                    model = (
                        "gpt-4o"
                        if provider == "openai"
                        else "claude-3-5-sonnet-20240620"
                    )
                    outcome = "SUCCESS" if i % 3 != 0 else "FAILURE"
                    resilience_score = (
                        1.0
                        if outcome == "SUCCESS"
                        else (0.5 if i % 3 == 1 else 0.2)
                    )
                    latency = (
                        random.uniform(100, 500)
                        if outcome == "SUCCESS"
                        else random.uniform(1000, 3000)
                    )

                    event_payload = {
                        "request_id": str(uuid.uuid4()),
                        "timestamp_utc": (
                            datetime.now(timezone.utc)
                            - timedelta(minutes=15 - i)
                        ).isoformat(),
                        "schema_version": 4,
                        "initial_prompt_hash": "abc",
                        "initial_prompt_preview": "...",
                        "outcome": outcome,
                        "total_latency_ms": latency,
                        "total_api_calls": 1,
                        "final_provider": provider,
                        "final_model": model,
                        "resilience_events": [
                            (
                                {
                                    "event_type": event_topics.API_CALL_FAILURE,
                                    "payload": {"error_type": "rate_limit"},
                                }
                                if outcome == "FAILURE"
                                else {}
                            )
                        ],
                        "mitigation_attempted": (i % 3 == 1),
                        "mitigation_succeeded": (
                            outcome == "MITIGATED_SUCCESS"
                        ),
                        "resilience_score": resilience_score,
                        "preferred_provider_requested": None,
                        "initial_selection_mode": "VALUE_DRIVEN",
                        "failover_reason": None,
                        "cost_cap_enforced": False,
                        "cost_cap_skip_reason": None,
                        "input_tokens": 50,
                        "output_tokens": 100,
                        "estimated_cost_usd": 0.001,
                    }
                    yield UniversalEventSchema(
                        event_type=event_topics.BIAS_LOG_ENTRY_CREATED,
                        event_topic="bias.ledger",
                        event_source="resilience.bias_ledger",
                        timestamp_utc=event_payload["timestamp_utc"],
                        severity="INFO",
                        payload=event_payload,
                    ).model_dump()

    mock_timeseries_db = MockTimeSeriesDB(MockConnectionManager())
    engine = LearningEngine(mock_timeseries_db)

    start_t = datetime.now(timezone.utc) - timedelta(days=1)
    end_t = datetime.now(timezone.utc)

    print("\n--- Analyzing Provider Performance ---")
    analysis_results = await engine.analyze_provider_performance(
        start_t, end_t
    )

    for result in analysis_results:
        print(
            f"\nProvider: {result.provider_name}, Model: {result.model_name}"
        )
        print(f"  Total Requests: {result.total_requests}")
        print(f"  Success Rate: {result.success_rate:.2f}")
        print(f"  Avg Latency: {result.avg_latency_ms:.2f}ms")
        print(f"  Avg Resilience Score: {result.avg_resilience_score:.2f}")
        print(f"  Error Distribution: {result.error_distribution}")
        print(f"  Failover Rate: {result.failover_rate:.2f}")
        print(
            f"  Mitigation Success Rate: {result.mitigation_success_rate:.2f}"
        )

    print("\nLearningEngine demo completed.")


if __name__ == "__main__":
    import asyncio
    import random  # Added for main demo
    import uuid  # Added for main demo

    asyncio.run(main())
