# 01_Framework_Core/telemetry/event_bus.py
import logging
from typing import Any, Callable, Dict, List

log = logging.getLogger(__name__)


class EventBus:
    """
    A simple event bus for publishing and subscribing to events.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        """
        Subscribe a handler function to an event type.

        Args:
            event_type: The type of event to subscribe to
            handler: The function to call when the event is published
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        log.debug(f"Subscribed handler to event type: {event_type}")

    def publish(self, event_type: str, payload: Dict[str, Any] = None):
        """
        Publish an event to all subscribers.

        Args:
            event_type: The type of event being published
            payload: Optional data to send with the event
        """
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    # Handle both sync and async handlers
                    if hasattr(handler, '__call__'):
                        handler(event_type, payload or {})
                except Exception as e:
                    log.error(f"Error in event handler for {event_type}: {e}")
        else:
            log.debug(f"No subscribers for event type: {event_type}")

    def shutdown(self):
        """Clear all subscribers"""
        self._subscribers.clear()
        log.info("EventBus shutdown complete")


# Global instance for backward compatibility
event_bus = EventBus()