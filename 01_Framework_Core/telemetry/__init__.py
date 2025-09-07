# Create this file: 01_Framework_Core/telemetry/__init__.py
# This will make telemetry a proper Python package that can be imported

# Make telemetry components available at package level
try:
    from . import event_topics
    from .core_logger import UniversalEventSchema, core_logger
    from .event_bus import EventBus
    from .telemetry_subscriber import TelemetrySubscriber
    from .time_series_db_interface import TimeSeriesDBInterface
except ImportError as e:
    import warnings
    warnings.warn(f"Some telemetry components could not be imported: {e}")

__all__ = [
    'event_topics',
    'UniversalEventSchema',
    'core_logger',
    'EventBus',
    'TelemetrySubscriber',
    'TimeSeriesDBInterface'
]