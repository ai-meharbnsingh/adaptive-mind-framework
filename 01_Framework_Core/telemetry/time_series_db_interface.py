# 01_Framework_Core/telemetry/time_series_db_interface.py

import sys
from abc import ABC, abstractmethod
from datetime import datetime

# Standardized path setup relative to the current file
# Assuming current file is in PROJECT_ROOT/01_Framework_Core/telemetry/
from pathlib import Path
from typing import Any, Dict, Iterator, List

CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent  # Points to project root
FRAMEWORK_CORE_PATH = PROJECT_ROOT / "01_Framework_Core" / "antifragile_framework"
DATABASE_LAYER_PATH = PROJECT_ROOT / "05_Database_Layer"


sys.path.insert(0, str(FRAMEWORK_CORE_PATH))
sys.path.insert(0, str(DATABASE_LAYER_PATH))
sys.path.insert(0, str(CURRENT_DIR))  # For sibling telemetry modules


class TimeSeriesDBInterface(ABC):
    """
    Abstract Base Class for a Time-Series Database interface.
    This interface defines the contract for any backend database that stores
    and provides query capabilities for time-series telemetry data.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initializes the database connection or resources for the time-series DB.
        This should set up any necessary pools or client connections.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Closes any open database connections or releases resources.
        This should be called during application shutdown for graceful termination.
        """
        pass

    @abstractmethod
    async def record_event(self, event_schema: Dict[str, Any]):
        """
        Records a single telemetry event into the time-series database.
        The event_schema should be a dictionary representation of a UniversalEventSchema.
        """
        pass

    @abstractmethod
    async def query_events(
        self,
        event_type: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Queries telemetry events of a specific type within a given time range.

        Args:
            event_type (str): The type of event to query (e.g., "api.call.success").
            start_time (datetime): The start timestamp for the query range (inclusive).
            end_time (datetime): The end timestamp for the query range (inclusive).
            limit (int): Maximum number of events to return.

        Returns:
            List[Dict[str, Any]]: A list of event dictionaries matching the criteria.
        """
        pass

    @abstractmethod
    async def query_events_generator(
        self,
        event_type: str,
        start_time: datetime,
        end_time: datetime,
        batch_size: int = 1000,
    ) -> Iterator[Dict[str, Any]]:
        """
        A generator that yields telemetry events in batches to handle large datasets
        without loading everything into memory at once.

        Args:
            event_type (str): The type of event to query.
            start_time (datetime): The start timestamp for the query range.
            end_time (datetime): The end timestamp for the query range.
            batch_size (int): Number of events to yield per batch.

        Yields:
            Dict[str, Any]: An event dictionary.
        """
        pass

    @abstractmethod
    async def aggregate_events(
        self,
        event_type: str,
        start_time: datetime,
        end_time: datetime,
        aggregate_by: str,
    ) -> List[Dict[str, Any]]:
        """
        Aggregates telemetry events based on a specified time interval or attribute.

        Args:
            event_type (str): The type of event to aggregate.
            start_time (datetime): The start timestamp for the aggregation period.
            end_time (datetime): The end timestamp for the aggregation period.
            aggregate_by (str): The aggregation key (e.g., "hour", "day", "provider", "total").

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents
                                  an aggregated bucket of metrics.
        """
        pass


# Example usage (for demonstrating the interface, not actual implementation)
async def main():
    class MockTimeSeriesDB(TimeSeriesDBInterface):
        """A simple mock implementation for testing the interface."""

        def __init__(self, name="MockDB"):
            self.name = name
            print(f"{self.name}: Initialized.")

        async def initialize(self):
            print(f"{self.name}: Connections initialized.")

        async def close(self):
            print(f"{self.name}: Connections closed.")

        async def record_event(self, event_schema: Dict[str, Any]):
            print(f"{self.name}: Recorded event: {event_schema.get('event_type')}")

        async def query_events(
            self,
            event_type: str,
            start_time: datetime,
            end_time: datetime,
            limit: int = 1000,
        ) -> List[Dict[str, Any]]:
            print(
                f"{self.name}: Querying {event_type} from {start_time} to {end_time} (mock data)."
            )
            return [
                {
                    "event_type": event_type,
                    "timestamp": datetime.now().isoformat(),
                    "payload": {"data": "mock"},
                }
                for _ in range(min(limit, 2))
            ]

        async def query_events_generator(
            self,
            event_type: str,
            start_time: datetime,
            end_time: datetime,
            batch_size: int = 1000,
        ) -> Iterator[Dict[str, Any]]:
            print(f"{self.name}: Generating {event_type} events (mock data).")
            for i in range(3):  # Yield 3 mock events
                yield {
                    "event_type": event_type,
                    "timestamp": datetime.now().isoformat(),
                    "payload": {"data": f"mock_batch_{i}"},
                }

        async def aggregate_events(
            self,
            event_type: str,
            start_time: datetime,
            end_time: datetime,
            aggregate_by: str,
        ) -> List[Dict[str, Any]]:
            print(
                f"{self.name}: Aggregating {event_type} by {aggregate_by} (mock data)."
            )
            return [{"aggregate_key": "mock_key", "count": 10, "avg_value": 5.5}]

    mock_db = MockTimeSeriesDB()

    await mock_db.initialize()
    await mock_db.record_event(
        {"event_type": "test_event", "timestamp": datetime.now().isoformat()}
    )
    await mock_db.query_events("test_event", datetime.now(), datetime.now())
    async for event in mock_db.query_events_generator(
        "test_event", datetime.now(), datetime.now()
    ):
        print(f"Generator yielded: {event}")
    await mock_db.aggregate_events("test_event", datetime.now(), datetime.now(), "hour")
    await mock_db.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
