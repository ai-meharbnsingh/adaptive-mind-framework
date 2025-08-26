# 03_Demo_Interface/real_time_metrics.py

"""
Real-Time Metrics Collector for Adaptive Mind Framework Demo Dashboard
SESSION 7 - Enhanced Demo Backend Integration (further refined in Session 8)

This module is responsible for:
1. Receiving and recording real-time demo execution metrics.
2. Aggregating these metrics from the TimeSeriesDB for dashboard display.
3. Providing live summary statistics and historical data for various charts.

Created: August 16, 2025 (Initial)
Updated: August 18, 2025 (Session 8 Refinement and PostgreSQL integration)
Author: Adaptive Mind Framework Team
Version: 2.1 (PostgreSQL-backed for Demo)
"""
import json
import random
import logging
import statistics  # For calculating averages etc.
import sys
import uuid  # For mock data generation
from datetime import datetime, timedelta, timezone

# Standardized path setup relative to the current file
# Assuming current file is in PROJECT_ROOT/03_Demo_Interface/
from pathlib import Path
from typing import Any, Dict, List, Optional

CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
FRAMEWORK_CORE_PATH = (
    PROJECT_ROOT / "01_Framework_Core" / "antifragile_framework"
)
DATABASE_LAYER_PATH = PROJECT_ROOT / "05_Database_Layer"
TELEMETRY_PATH = PROJECT_ROOT / "01_Framework_Core" / "telemetry"

# Add paths to sys.path
sys.path.insert(0, str(FRAMEWORK_CORE_PATH))
sys.path.insert(0, str(DATABASE_LAYER_PATH))
sys.path.insert(0, str(TELEMETRY_PATH))
sys.path.insert(
    0, str(CURRENT_DIR)
)  # For sibling modules within 03_Demo_Interface

# Import TimeSeriesDBInterface (abstract base class, implemented by PostgreSQLTimeSeriesDB)
# and UniversalEventSchema for structured logging of demo metrics
try:
    from telemetry import event_topics  # For specific event types
    from telemetry.core_logger import UniversalEventSchema
    from telemetry.time_series_db_interface import TimeSeriesDBInterface

    DB_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logging.warning(
        f"Failed to import core telemetry components: {e}. RealTimeMetricsCollector will run in mock mode.",
        exc_info=True,
    )
    DB_INTEGRATION_AVAILABLE = False

    # Mock classes if core telemetry is not available
    class MockTimeSeriesDBInterface:
        def __init__(self, conn_manager):
            self.records = []

        async def initialize(self):
            logging.warning("Mock TimeSeriesDBInterface initialized.")
            pass

        async def close(self):
            pass

        async def record_event(self, event_schema: Dict[str, Any]):
            self.records.append(event_schema)
            logging.debug(
                f"Mock DB recorded: {event_schema.get('event_type')}"
            )

        async def query_events(
            self,
            event_type: str,
            start_time: datetime,
            end_time: datetime,
            limit: int = 1000,
        ) -> List[Dict[str, Any]]:
            return [
                r
                for r in self.records
                if r["event_type"] == event_type
                and datetime.fromisoformat(r["timestamp_utc"]).replace(
                    tzinfo=timezone.utc
                )
                >= start_time
                and datetime.fromisoformat(r["timestamp_utc"]).replace(
                    tzinfo=timezone.utc
                )
                <= end_time
            ]

        async def aggregate_events(
            self,
            event_type: str,
            start_time: datetime,
            end_time: datetime,
            aggregate_by: str,
        ) -> List[Dict[str, Any]]:
            # Simplified mock aggregation for demo
            if aggregate_by == "total":
                relevant_events = [
                    e
                    for e in self.records
                    if e["event_type"] == event_type
                    and datetime.fromisoformat(e["timestamp_utc"]).replace(
                        tzinfo=timezone.utc
                    )
                    >= start_time
                    and datetime.fromisoformat(e["timestamp_utc"]).replace(
                        tzinfo=timezone.utc
                    )
                    <= end_time
                ]
                total_requests = len(relevant_events)
                total_cost_usd = sum(
                    e["payload"].get("cost_estimate", 0.0)
                    for e in relevant_events
                )
                total_failovers = sum(
                    1
                    for e in relevant_events
                    if e["payload"].get("failover_occurred", False)
                )
                avg_response_time_ms = (
                    statistics.mean(
                        [
                            e["payload"].get("response_time_ms", 0.0)
                            for e in relevant_events
                        ]
                    )
                    if relevant_events
                    else 0.0
                )
                latest_bias_score = (
                    relevant_events[-1]["payload"].get("bias_score", 0.0)
                    if relevant_events
                    else 0.0
                )
                return [
                    {
                        "total_requests": total_requests,
                        "total_cost_usd": total_cost_usd,
                        "total_failovers": total_failovers,
                        "avg_response_time_ms": avg_response_time_ms,
                        "latest_bias_score": latest_bias_score,
                    }
                ]
            elif aggregate_by == "hour":
                mock_data = []
                # Generate mock data for the current hour
                now = datetime.now(timezone.utc)
                for i in range(24):  # Last 24 hours
                    ts_bucket = (
                        (now - timedelta(hours=i))
                        .replace(minute=0, second=0, microsecond=0)
                        .isoformat()
                    )
                    mock_data.append(
                        {
                            "time_bucket": ts_bucket,
                            "avg_response_time_ms": random.uniform(150, 400),
                            "total_cost_usd": random.uniform(0.005, 0.045),
                            "failover_count": random.randint(0, 4),
                        }
                    )
                return mock_data
            elif aggregate_by == "provider":
                mock_data = []
                providers = ["openai", "anthropic", "google"]
                for p in providers:
                    mock_data.append(
                        {
                            "provider_used": p,
                            "total_cost_usd": random.uniform(0.1, 0.5),
                        }
                    )
                return mock_data
            return []

    class UniversalEventSchema:
        def __init__(
            self, event_type, event_source, timestamp_utc, severity, payload
        ):
            self.event_type = event_type
            self.event_source = event_source
            self.timestamp_utc = timestamp_utc
            self.severity = severity
            self.payload = payload

        def model_dump(self):
            return {
                "event_type": self.event_type,
                "event_source": self.event_source,
                "timestamp_utc": self.timestamp_utc,
                "severity": self.severity,
                "payload": self.payload,
            }

    class EventTopics:  # Mock selected topics
        DEMO_METRIC_RECORDED = "demo.metric.recorded"

    event_topics = EventTopics()

# Enterprise logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RealTimeMetricsCollector:
    """
    Collects, aggregates, and provides real-time and historical metrics for the demo dashboard.
    It integrates with the TimeSeriesDB for data persistence and retrieval.
    """

    class MetricType:
        """Defines standardized metric event types for the TimeSeriesDB."""

        DEMO_EXECUTION = "demo.execution.recorded"
        SYSTEM_HEALTH = "system.health.snapshot"
        # Add other metric types as needed

    def __init__(self):
        self.timeseries_db: Optional[TimeSeriesDBInterface] = None
        logger.info("RealTimeMetricsCollector initialized.")

    async def initialize(self, timeseries_db: TimeSeriesDBInterface):
        """
        Initializes the metrics collector with a TimeSeriesDB instance.
        This must be called at application startup.
        """
        if not DB_INTEGRATION_AVAILABLE:
            logger.warning(
                "DB integration not available. RealTimeMetricsCollector is running in mock mode."
            )
            self.timeseries_db = MockTimeSeriesDBInterface(
                None
            )  # Pass None for conn_manager in mock
            return

        if not isinstance(timeseries_db, TimeSeriesDBInterface):
            raise TypeError(
                "timeseries_db must be an instance of TimeSeriesDBInterface"
            )
        self.timeseries_db = timeseries_db
        # We don't call timeseries_db.initialize() here, as it's assumed the main lifespan
        # of the demo backend will initialize the shared TimeSeriesDBInterface.
        logger.info(
            "RealTimeMetricsCollector connected to provided TimeSeriesDB instance."
        )

    async def record_demo_execution(
        self,
        session_id: str,
        mode: str,
        use_case: str,
        response_time_ms: float,
        cost_estimate: float,
        provider_used: str,
        failover_occurred: bool = False,
        bias_score: Optional[float] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,  # Added for completeness
        **kwargs,
    ):
        """
        Records the outcome of a single demo execution, including performance, cost,
        and resilience metrics. This data is pushed to the TimeSeriesDB.
        """
        if self.timeseries_db is None:
            logger.warning(
                "TimeSeriesDB not initialized. Cannot record demo execution metrics."
            )
            return

        event_payload = {
            "session_id": session_id,
            "mode": mode,
            "use_case": use_case,
            "response_time_ms": response_time_ms,
            "cost_estimate": cost_estimate,
            "provider_used": provider_used,
            "failover_occurred": failover_occurred,
            "bias_score": bias_score,
            "success": (
                True if response_time_ms > 0 else False
            ),  # Basic success indicator for recording
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            **kwargs,  # Allow for additional flexible data
        }

        event_schema = UniversalEventSchema(
            event_type=self.MetricType.DEMO_EXECUTION,
            # Use a specific topic for demo metrics
            event_topic=event_topics.DEMO_METRIC_RECORDED,
            event_source=self.__class__.__name__,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            severity="INFO",
            payload=event_payload,
        ).model_dump()  # Use model_dump to get dict representation

        try:
            await self.timeseries_db.record_event(event_schema)
            logger.debug(
                f"Recorded demo execution metric for session {session_id}."
            )
        except Exception as e:
            logger.error(
                f"Failed to record demo execution metric for session {session_id}: {e}",
                exc_info=True,
            )

    async def get_live_metrics(self) -> Dict[str, Any]:
        """
        Fetches the most recent live metrics from the TimeSeriesDB for instant dashboard updates.
        This provides a snapshot of current system health and performance.
        """
        if self.timeseries_db is None:
            logger.warning(
                "TimeSeriesDB not initialized. Cannot fetch live metrics."
            )
            return self._get_mock_live_metrics()

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(
            minutes=5
        )  # Look at last 5 minutes for "live" data

        try:
            # Aggregate total metrics for recent period
            total_metrics_raw = await self.timeseries_db.aggregate_events(
                event_type=self.MetricType.DEMO_EXECUTION,
                start_time=start_time,
                end_time=end_time,
                aggregate_by="total",
            )
            # total_metrics_raw will be a list containing one dict, or empty/mock if no data
            total_metrics = total_metrics_raw[0] if total_metrics_raw else {}

            # These values might be None if no data, ensure default to 0.0 or 0
            total_requests = total_metrics.get("total_requests", 0)
            avg_response_time_ms = total_metrics.get(
                "avg_response_time_ms", 0.0
            )
            total_cost_usd = total_metrics.get("total_cost_usd", 0.0)
            total_failovers = total_metrics.get("total_failovers", 0)
            latest_bias_score = total_metrics.get("latest_bias_score", 0.0)

            # Calculate additional summary metrics
            avg_cost_per_request = (
                (total_cost_usd / total_requests)
                if total_requests > 0
                else 0.0
            )
            failover_rate = (
                (total_failovers / total_requests) * 100
                if total_requests > 0
                else 0.0
            )

            return {
                "total_requests": total_requests,
                "avg_response_time_ms": round(avg_response_time_ms, 2),
                "total_cost_usd": round(total_cost_usd, 4),
                "avg_cost_per_request": round(avg_cost_per_request, 5),
                "total_failovers": total_failovers,
                "failover_rate_percent": round(failover_rate, 2),
                "latest_bias_score": round(latest_bias_score, 3),
            }
        except Exception as e:
            logger.error(
                f"Failed to get live metrics from TimeSeriesDB: {e}",
                exc_info=True,
            )
            return self._get_mock_live_metrics()

    def _get_mock_live_metrics(self) -> Dict[str, Any]:
        """Provides mock live metrics for testing or when DB integration is unavailable."""
        logger.warning("Providing mock live metrics.")
        return {
            "total_requests": random.randint(100, 500),
            "avg_response_time_ms": round(random.uniform(200, 400), 2),
            "total_cost_usd": round(random.uniform(0.5, 2.5), 4),
            "avg_cost_per_request": round(random.uniform(0.005, 0.008), 5),
            "total_failovers": random.randint(0, 5),
            "failover_rate_percent": round(random.uniform(0.0, 5.0), 2),
            "latest_bias_score": round(random.uniform(0.05, 0.15), 3),
        }

    async def get_aggregated_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        aggregate_by: str,  # "hour", "day", "provider", "total"
        metric_type: str = MetricType.DEMO_EXECUTION,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves aggregated historical metrics for a given time window.
        """
        if self.timeseries_db is None:
            logger.warning(
                "TimeSeriesDB not initialized. Cannot get aggregated metrics."
            )
            return {"data": []}

        try:
            # The session_id filtering happens within the TimeSeriesDB.aggregate_events method if supported
            # For simplicity in this demo, it's assumed aggregate_events handles `session_id` filter
            # or the data is small enough that filtering by session_id is a post-processing step if needed.
            results = await self.timeseries_db.aggregate_events(
                event_type=metric_type,
                start_time=start_time,
                end_time=end_time,
                aggregate_by=aggregate_by,
            )
            # If aggregating by 'total', results is a list with one dict, we need to return just that dict inside 'data'
            if aggregate_by == "total" and results:
                return {"data": results}  # Already in correct format

            return {"data": results}
        except Exception as e:
            logger.error(
                f"Failed to get aggregated metrics for {metric_type}, by {aggregate_by}: {e}",
                exc_info=True,
            )
            return {"data": []}

    async def get_performance_summary(
        self,
    ) -> Any:  # Returns a simple object with attributes
        """
        Provides a high-level summary of performance metrics for dashboard cards.
        This is a simplified object tailored for quick access.
        """
        live_metrics = await self.get_live_metrics()

        class Summary:
            def __init__(self, metrics: Dict[str, Any]):
                self.total_requests = metrics.get("total_requests", 0)
                self.total_cost = metrics.get("total_cost_usd", 0.0)
                self.avg_cost_per_request = metrics.get(
                    "avg_cost_per_request", 0.0
                )
                self.failover_rate = metrics.get(
                    "failover_rate_percent", 0.0
                )  # This is percentage
                self.total_failovers = metrics.get("total_failovers", 0)
                self.avg_response_time_ms = metrics.get(
                    "avg_response_time_ms", 0.0
                )

                # Heuristic for demo uptime and efficiency
                self.system_uptime_percent = 100.0 - (
                    self.failover_rate / 2
                )  # Reduce impact of failover rate
                if self.total_requests == 0:
                    self.system_uptime_percent = (
                        99.99  # Assume high uptime if no requests
                    )
                self.system_uptime_percent = max(
                    95.0, min(99.99, self.system_uptime_percent)
                )  # Clamp to realistic range

                # Mock active providers, etc.
                self.total_providers = 5  # Fixed for demo
                self.active_providers_count = 3  # Fixed for demo

        return Summary(live_metrics)


if __name__ == "__main__":
    import asyncio

    from connection_manager import (  # For real DB test
        PostgreSQLConnectionManager,
    )

    async def main():
        print("Starting RealTimeMetricsCollector demo...")

        # For a real database test, ensure PostgreSQL is running and has telemetry_events data
        conn_manager = PostgreSQLConnectionManager()
        timeseries_db = TimeSeriesDBInterface(
            conn_manager
        )  # Pass conn_manager to TimeSeriesDBInterface
        metrics_collector = RealTimeMetricsCollector()
        await metrics_collector.initialize(
            timeseries_db
        )  # Initialize with the real TimeSeriesDBInterface

        try:
            # Simulate recording some demo executions
            print("\n--- Recording Sample Demo Execution Metrics ---")
            for _ in range(5):
                await metrics_collector.record_demo_execution(
                    session_id=str(uuid.uuid4()),
                    mode="hosted",
                    use_case=random.choice(["general", "customer_service"]),
                    response_time_ms=random.uniform(100, 500),
                    cost_estimate=random.uniform(0.001, 0.015),
                    provider_used=random.choice(
                        ["openai", "anthropic", "google"]
                    ),
                    failover_occurred=random.random() < 0.1,
                    bias_score=random.uniform(0.05, 0.25),
                )
                await asyncio.sleep(0.1)  # Small delay

            # Test get_live_metrics
            print("\n--- Live Metrics (Last 5 minutes) ---")
            live_metrics = await metrics_collector.get_live_metrics()
            print(json.dumps(live_metrics, indent=2))

            # Test get_performance_summary
            print("\n--- Performance Summary ---")
            summary = await metrics_collector.get_performance_summary()
            print(f"Total Requests: {summary.total_requests}")
            print(f"Avg Response Time: {summary.avg_response_time_ms:.2f}ms")
            print(f"Total Cost: ${summary.total_cost:.4f}")
            print(f"Failover Rate: {summary.failover_rate:.2f}%")
            print(f"System Uptime: {summary.system_uptime_percent:.2f}%")

            # Test get_aggregated_metrics by hour (last 24 hours)
            print("\n--- Aggregated Metrics by Hour (Last 24h) ---")
            hourly_data = await metrics_collector.get_aggregated_metrics(
                start_time=datetime.now(timezone.utc) - timedelta(hours=24),
                end_time=datetime.now(timezone.utc),
                aggregate_by="hour",
                metric_type=metrics_collector.MetricType.DEMO_EXECUTION,
            )
            print(f"Hourly Data Count: {len(hourly_data['data'])}")
            if hourly_data["data"]:
                print(f"First Entry: {hourly_data['data'][0]}")
                print(f"Last Entry: {hourly_data['data'][-1]}")

            # Test aggregated metrics by provider
            print("\n--- Aggregated Metrics by Provider ---")
            provider_data = await metrics_collector.get_aggregated_metrics(
                start_time=datetime.now(timezone.utc) - timedelta(days=7),
                end_time=datetime.now(timezone.utc),
                aggregate_by="provider",
                metric_type=metrics_collector.MetricType.DEMO_EXECUTION,
            )
            print(f"Provider Data: {provider_data['data']}")

        except Exception as e:
            logger.error(f"Demo error: {e}", exc_info=True)
        finally:
            # Ensure database connections are closed
            await timeseries_db.close()
            print("\nRealTimeMetricsCollector demo completed.")

    asyncio.run(main())
