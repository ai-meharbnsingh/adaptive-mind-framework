# telemetry/telemetry_subscriber.py

import asyncio
import logging
from datetime import datetime, timezone
from telemetry.event_bus import EventBus
from telemetry.time_series_db_interface import TimeSeriesDBInterface
from telemetry.core_logger import core_logger, UniversalEventSchema
from telemetry import event_topics


# THE ERRONEOUS SELF-IMPORT LINE HAS BEEN REMOVED FROM HERE

class TelemetrySubscriber:
    """
    Subscribes to specific events from the EventBus and persists them
    to a time-series database.
    """

    def __init__(self, event_bus: EventBus, db_interface: TimeSeriesDBInterface, log_level: int = logging.INFO):
        if not isinstance(event_bus, EventBus):
            raise TypeError("event_bus must be an instance of EventBus")
        if not isinstance(db_interface, TimeSeriesDBInterface):
            raise TypeError("db_interface must be an instance of TimeSeriesDBInterface")

        self.event_bus = event_bus
        self.db_interface = db_interface
        self.logger = core_logger
        self.log_level = log_level
        self._subscribed_topics = []

    def subscribe_to_all_events(self):
        """Subscribes the persistence handler to all defined event topics."""
        all_topics = [
            topic for topic in event_topics.__dict__.values()
            if isinstance(topic, str) and not topic.startswith("__")
        ]
        for topic in all_topics:
            self.event_bus.subscribe(topic, self.persist_event)
            self._subscribed_topics.append(topic)

        init_event = UniversalEventSchema(
            event_type="TELEMETRY_SUBSCRIBER_INIT",
            event_source=self.__class__.__name__,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            severity="INFO",
            payload={
                "message": f"TelemetrySubscriber initialization complete. Subscribed to {len(self._subscribed_topics)} topics."}
        )
        self.logger.log(init_event)

    async def persist_event(self, event_name: str, event_data: dict):
        """
        The event handler function that receives events and writes them to the DB.
        """
        try:
            event_data_with_name = event_data.copy()
            event_data_with_name['event_name'] = event_name
            await self.db_interface.write_event(event_data_with_name)

            if self.log_level <= logging.DEBUG:
                success_event = UniversalEventSchema(
                    event_type="EVENT_PERSISTENCE_SUCCESS",
                    event_source=self.__class__.__name__,
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    severity="DEBUG",
                    payload={"event_name": event_name, "message": f"Successfully persisted event '{event_name}'."}
                )
                self.logger.log(success_event)
        except Exception as e:
            failure_event = UniversalEventSchema(
                event_type="EVENT_PERSISTENCE_FAILURE",
                event_source=self.__class__.__name__,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                severity="ERROR",
                payload={
                    "event_name": event_name,
                    "message": f"Failed to persist event '{event_name}' to time-series DB.",
                    "error_details": str(e)
                }
            )
            self.logger.log(failure_event)

    def get_subscribed_topics(self) -> list:
        """Returns a list of topics this subscriber is listening to."""
        return self._subscribed_topics