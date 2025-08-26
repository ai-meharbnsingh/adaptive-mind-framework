# tests/telemetry/test_telemetry_subscriber.py

import asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest
from telemetry import event_topics
from telemetry.core_logger import UniversalEventSchema
from telemetry.event_bus import EventBus
from telemetry.telemetry_subscriber import TelemetrySubscriber
from telemetry.time_series_db_interface import TimeSeriesDBInterface


@pytest.fixture
def mock_event_bus():
    # Use a real EventBus instance for testing subscription logic
    return EventBus()


@pytest.fixture
def mock_db_interface():
    mock = Mock(spec=TimeSeriesDBInterface)
    mock.write_event = AsyncMock()
    return mock


@pytest.fixture(autouse=True)
def mock_logger():
    # Patch the singleton instance directly where it's imported
    with patch(
        "telemetry.telemetry_subscriber.core_logger"
    ) as mock_logger_instance:
        yield mock_logger_instance


@pytest.mark.asyncio
async def test_subscriber_initialization(mock_event_bus, mock_db_interface):
    """Test that the subscriber initializes correctly."""
    subscriber = TelemetrySubscriber(mock_event_bus, mock_db_interface)
    assert subscriber.event_bus is mock_event_bus
    assert subscriber.db_interface is mock_db_interface
    assert subscriber.get_subscribed_topics() == []


@pytest.mark.asyncio
async def test_subscribe_to_all_events(
    mock_event_bus, mock_db_interface, mock_logger
):
    """Test that the subscriber correctly subscribes to all defined topics."""
    subscriber = TelemetrySubscriber(mock_event_bus, mock_db_interface)
    subscriber.subscribe_to_all_events()

    all_topic_values = {
        v
        for v in vars(event_topics).values()
        if isinstance(v, str) and not v.startswith("__")
    }

    assert set(subscriber.get_subscribed_topics()) == all_topic_values

    # CORRECTED: The internal attribute is `_subscribers`, not `_handlers` or `_listeners`.
    assert set(mock_event_bus._subscribers.keys()) == all_topic_values


@pytest.mark.asyncio
async def test_persist_event_success(mock_event_bus, mock_db_interface):
    """Test the successful persistence of an event."""
    subscriber = TelemetrySubscriber(mock_event_bus, mock_db_interface)

    event_name = "test.event.success"
    event_data = {"key": "value", "source": "test"}

    await subscriber.persist_event(event_name, event_data)

    mock_db_interface.write_event.assert_awaited_once()

    call_args, _ = mock_db_interface.write_event.call_args
    persisted_data = call_args[0]
    assert persisted_data["event_name"] == event_name
    assert persisted_data["key"] == "value"


@pytest.mark.asyncio
async def test_persist_event_db_failure_is_handled_gracefully(
    mock_event_bus, mock_db_interface, mock_logger
):
    """Test that a DB failure is handled gracefully without raising an exception."""
    subscriber = TelemetrySubscriber(mock_event_bus, mock_db_interface)

    db_error = ConnectionError("Database connection failed")
    mock_db_interface.write_event.side_effect = db_error

    event_name = "test.event.failure"

    await subscriber.persist_event(event_name, {"key": "value"})

    mock_db_interface.write_event.assert_awaited_once()
    mock_logger.log.assert_called_once()

    call_args, _ = mock_logger.log.call_args
    logged_event = call_args[0]

    assert isinstance(logged_event, UniversalEventSchema)
    assert logged_event.severity == "ERROR"
    assert "Failed to persist event" in logged_event.payload["message"]
    assert logged_event.payload["error_details"] == str(db_error)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "log_level, expect_log_call",
    [
        (logging.DEBUG, True),
        (logging.INFO, False),
    ],
)
async def test_success_logging_is_configurable(
    mock_event_bus, mock_db_interface, mock_logger, log_level, expect_log_call
):
    """Test that debug-level success logging is controlled by the log_level parameter."""
    subscriber = TelemetrySubscriber(
        mock_event_bus, mock_db_interface, log_level=log_level
    )

    await subscriber.persist_event("test.event.success", {"key": "value"})

    was_called = any(
        isinstance(arg, UniversalEventSchema) and arg.severity == "DEBUG"
        for call in mock_logger.log.call_args_list
        for arg in call.args
    )
    assert was_called == expect_log_call
