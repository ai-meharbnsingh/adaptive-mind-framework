# telemetry/time_series_db_interface.py

import time
import logging
import threading
from queue import Queue, Empty
from typing import Dict, Any, List, Optional, Iterator
from urllib.parse import urlparse, urlunparse
from datetime import datetime

from sqlalchemy import create_engine, text, Table, MetaData, Column, String, JSON, TIMESTAMP, insert, select
from sqlalchemy.exc import SQLAlchemyError

from telemetry.event_bus import event_bus
from telemetry.core_logger import UniversalEventSchema

log = logging.getLogger(__name__)


def _mask_db_url(db_url: str) -> str:
    """Masks the password in a database URL for safe logging."""
    try:
        parsed = urlparse(db_url)
        if parsed.password:
            safe_netloc = f"{parsed.username}:***@{parsed.hostname}:{parsed.port}"
            return urlunparse(parsed._replace(netloc=safe_netloc))
        return db_url
    except Exception:
        return "Malformed DB URL"


class TimeSeriesDBInterface:
    """
    Handles the connection and data ingestion and retrieval for a time-series database.
    """

    def __init__(self, db_url: str, table_name: str = "telemetry_events",
                 batch_size: int = 100, flush_interval_seconds: int = 10):

        self.safe_db_url = _mask_db_url(db_url)
        log.info(f"Initializing TimeSeriesDBInterface for DB: {self.safe_db_url}")

        self.engine = create_engine(db_url)
        self.table_name = table_name
        self.batch_size = batch_size
        self.flush_interval = flush_interval_seconds

        self.queue = Queue()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._batch_processor, daemon=True)

        self._metadata = MetaData()
        self._events_table = self._define_table()
        self._create_table_if_not_exists()

    def _define_table(self) -> Table:
        """Defines the SQLAlchemy Table object for telemetry events.
        Implicitly, timestamp_utc is primary key and will be indexed.
        event_type is explicitly indexed.
        """
        return Table(
            self.table_name,
            self._metadata,
            Column('timestamp_utc', TIMESTAMP, primary_key=True),
            Column('event_type', String(255), index=True),  # Explicitly indexed for query efficiency
            Column('event_source', String(255), index=True),
            Column('severity', String(50)),
            Column('payload', JSON)
        )

    def _create_table_if_not_exists(self):
        """Creates the telemetry table in the database if it doesn't already exist."""
        try:
            with self.engine.connect() as connection:
                self._metadata.create_all(connection)
                log.info(f"Table '{self.table_name}' is ready.")
        except SQLAlchemyError as e:
            log.error(f"Failed to create or verify table '{self.table_name}' in DB {self.safe_db_url}: {e}")
            raise

    def start(self):
        if not self._worker_thread.is_alive():
            self._stop_event.clear()
            self._worker_thread.start()
            log.info("TimeSeriesDBInterface worker thread started.")

    def stop(self):
        log.info("Stopping TimeSeriesDBInterface worker thread.")
        self._stop_event.set()
        self._worker_thread.join(timeout=self.flush_interval + 2)
        self._flush_queue()
        log.info("TimeSeriesDBInterface worker thread stopped.")

    def _batch_processor(self):
        last_flush_time = time.monotonic()
        while not self._stop_event.is_set():
            try:
                time_since_last_flush = time.monotonic() - last_flush_time
                if time_since_last_flush >= self.flush_interval and self.queue.qsize() > 0:
                    self._flush_queue()
                    last_flush_time = time.monotonic()
                time.sleep(0.1)
            except Exception as e:
                log.exception(f"Error in batch processor loop: {e}")

    def _flush_queue(self):
        batch = []
        while len(batch) < self.batch_size:
            try:
                batch.append(self.queue.get_nowait())
            except Empty:
                break
        if not batch: return

        log.info(f"Flushing batch of {len(batch)} events to the database.")
        with self._connect_with_retry() as connection:
            if connection:
                try:
                    stmt = insert(self._events_table)
                    connection.execute(stmt, batch)
                    connection.commit()
                except SQLAlchemyError as e:
                    log.error(f"Database error during batch flush: {e}. Returning batch to queue.")
                    for item in batch: self.queue.put(item)
            else:
                log.error("Failed to connect to the database after retries. Batch returned to queue.")
                for item in batch: self.queue.put(item)

    def _connect_with_retry(self, retries=3, backoff_factor=2):
        attempt = 0
        while attempt < retries:
            try:
                return self.engine.connect()
            except SQLAlchemyError as e:
                attempt += 1
                sleep_time = backoff_factor ** attempt
                log.warning(
                    f"DB connection failed (Attempt {attempt}/{retries}). Retrying in {sleep_time}s. Error: {e}")
                time.sleep(sleep_time)
        return None

    def ingest_event(self, event_data: Dict[str, Any]):
        self.queue.put(event_data)
        if self.queue.qsize() >= self.batch_size:
            self._flush_queue()

    def event_bus_subscriber(self, payload: UniversalEventSchema):
        try:
            if not isinstance(payload, UniversalEventSchema):
                log.warning(f"Received non-UniversalEventSchema payload from event bus: {type(payload)}")
                return
            event_for_db = {
                "timestamp_utc": payload.timestamp_utc,
                "event_type": payload.event_type,
                "event_source": payload.event_source,
                "severity": payload.severity,
                "payload": payload.payload
            }
            self.ingest_event(event_for_db)
        except Exception as e:
            log.exception(f"Error in event_bus_subscriber: {e}")

    def query_events_generator(self,
                               event_type: str,
                               start_time: datetime,
                               end_time: datetime,
                               limit: Optional[int] = None,
                               offset: Optional[int] = None,
                               batch_size: int = 100) -> Iterator[Dict[str, Any]]:
        """
        Queries events from the database as a generator, yielding them in batches.
        This prevents loading large datasets into memory at once.

        Args:
            event_type: The type of event to query (e.g., event_topics.BIAS_LOG_ENTRY_CREATED).
            start_time: The start of the time range (inclusive, UTC datetime).
            end_time: The end of the time range (inclusive, UTC datetime).
            limit: Optional maximum number of events to retrieve.
            offset: Optional number of events to skip from the beginning.
            batch_size: Number of events to yield in each internal iteration batch.

        Yields:
            Dictionaries representing the raw event data from the database.
        """
        try:
            with self._connect_with_retry() as connection:
                if connection is None:
                    log.error("Failed to establish database connection for query_events_generator after retries.")
                    return  # Yield nothing if connection fails

                stmt = select(self._events_table.c.timestamp_utc,
                              self._events_table.c.event_type,
                              self._events_table.c.event_source,
                              self._events_table.c.severity,
                              self._events_table.c.payload).where(
                    self._events_table.c.event_type == event_type,
                    self._events_table.c.timestamp_utc >= start_time,
                    self._events_table.c.timestamp_utc <= end_time
                ).order_by(self._events_table.c.timestamp_utc)

                if limit is not None:
                    stmt = stmt.limit(limit)
                if offset is not None:
                    stmt = stmt.offset(offset)

                # Execute the query and iterate in batches
                # For SQLite, the result set is typically in-memory for small-medium queries.
                # For larger databases, this pattern is crucial for memory efficiency.
                result = connection.execute(stmt)

                while True:
                    batch = result.fetchmany(batch_size)
                    if not batch:
                        break
                    for row in batch:
                        yield {
                            "timestamp_utc": row.timestamp_utc,
                            "event_type": row.event_type,
                            "event_source": row.event_source,
                            "severity": row.severity,
                            "payload": row.payload  # This is already deserialized JSON in SQLite, or will be dict
                        }
        except SQLAlchemyError as e:
            log.error(f"Database error during query_events_generator: {e}", exc_info=True)
            # Do not re-raise, gracefully stop yielding
        except Exception as e:
            log.error(f"Unexpected error in query_events_generator: {e}", exc_info=True)
            # Do not re-raise, gracefully stop yielding


def initialize_and_subscribe_db_interface(db_url: str, **kwargs) -> TimeSeriesDBInterface:
    db_interface = TimeSeriesDBInterface(db_url=db_url, **kwargs)
    event_bus.subscribe("LOG_EVENT", db_interface.event_bus_subscriber)
    db_interface.start()
    log.info("TimeSeriesDBInterface has subscribed to 'LOG_EVENT' on the event bus.")
    return db_interface
