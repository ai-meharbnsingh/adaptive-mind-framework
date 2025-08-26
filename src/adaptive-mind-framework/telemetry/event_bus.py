# telemetry/event_bus.py

import logging
import threading
from collections import defaultdict
from typing import Callable, Any, Dict, List
from concurrent.futures import ThreadPoolExecutor

log = logging.getLogger(__name__)


class EventBus:
    """
    A thread-safe, in-process publish-subscribe event bus.

    This class implements the Singleton pattern to ensure that there is only
    one event bus instance throughout the application, providing a central
    point for decoupled communication between different components.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, max_async_workers: int = 5):
        """
        Initializes the EventBus.

        Args:
            max_async_workers (int): The number of worker threads for handling
                                     asynchronous event dispatch.
        """
        if not hasattr(self, '_initialized'):
            self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
            self._lock = threading.Lock()
            self._executor = ThreadPoolExecutor(max_workers=max_async_workers)
            self._initialized = True
            log.info(f"EventBus initialized with {max_async_workers} async workers.")

    def subscribe(self, event_type: str, callback: Callable):
        """
        Subscribes a callback function to a specific event type.

        Args:
            event_type (str): The name of the event to subscribe to.
            callback (Callable): The function to be called when the event is published.
                                 It should accept a single argument (the event payload).
        """
        if not callable(callback):
            log.error(f"Attempted to subscribe a non-callable object to event '{event_type}'.")
            return

        with self._lock:
            self._subscribers[event_type].append(callback)
            log.debug(f"Callback {callback.__name__} subscribed to event '{event_type}'.")

    def publish(self, event_type: str, payload: Any, dispatch_async: bool = True):
        """
        Publishes an event to all subscribed listeners.

        Args:
            event_type (str): The name of the event being published.
            payload (Any): The data/payload to pass to the subscribers.
            dispatch_async (bool): If True, subscribers are called in a separate
                                   thread pool to avoid blocking the publisher.
                                   If False, subscribers are called sequentially
                                   and synchronously.
        """
        with self._lock:
            callbacks = self._subscribers.get(event_type, []).copy()

        if not callbacks:
            log.debug(f"Event '{event_type}' published, but no subscribers found.")
            return

        log.info(f"Publishing event '{event_type}' to {len(callbacks)} subscriber(s).")
        for callback in callbacks:
            if dispatch_async:
                try:
                    # Submit the callback to the thread pool for asynchronous execution
                    self._executor.submit(self._safe_execute, callback, payload)
                except RuntimeError as e:
                    # CORRECTED: Gracefully handle the race condition where the bus is shutting down
                    # while a final event (e.g., from a finally block) is being published.
                    log.warning(f"Could not publish event '{event_type}' asynchronously: {e}. The event bus may be shutting down.")
            else:
                self._safe_execute(callback, payload)

    def _safe_execute(self, callback: Callable, payload: Any):
        """
        A wrapper to execute a subscriber callback with robust error handling.
        This prevents one faulty subscriber from crashing the entire event bus.
        """
        try:
            callback(payload)
        except Exception as e:
            log.exception(
                f"Error executing callback '{callback.__name__}' for event. Payload: {payload}. Error: {e}"
            )

    def shutdown(self, wait: bool = True):
        """
        Shuts down the asynchronous event dispatcher's thread pool.
        This should be called during a graceful application shutdown.
        """
        log.info("EventBus shutting down thread pool executor.")
        self._executor.shutdown(wait=wait)


# --- Singleton Instance ---
event_bus = EventBus()