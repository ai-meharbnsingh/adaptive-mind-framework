# 01_Framework_Core/telemetry/core_logger.py

import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Standardized path setup relative to the current file
# Assuming current file is in PROJECT_ROOT/01_Framework_Core/telemetry/
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
FRAMEWORK_CORE_PATH = (
    PROJECT_ROOT / "01_Framework_Core" / "antifragile_framework" / "core"
)

sys.path.insert(0, str(FRAMEWORK_CORE_PATH))

# Import UniversalEventSchema from its centralized location
try:
    from schemas import UniversalEventSchema

    SCHEMA_AVAILABLE = True
except ImportError as e:
    logging.warning(
        f"Warning: Failed to import UniversalEventSchema from core schemas: {e}. Using fallback schema."
    )
    SCHEMA_AVAILABLE = False

    # Define a minimal fallback schema to prevent crashes
    from pydantic import BaseModel, Field

    class UniversalEventSchema(BaseModel):
        """Fallback UniversalEventSchema if core schemas not available"""

        event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
        event_type: str = "unknown.event"
        event_topic: str = "unknown.topic"
        event_source: str = "unknown.source"
        timestamp_utc: str = Field(
            default_factory=lambda: datetime.now(timezone.utc).isoformat()
        )
        severity: str = "INFO"
        payload: Dict[str, Any] = Field(default_factory=dict)
        parent_event_id: Optional[str] = None


# Configure the logger for the telemetry system
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


class CoreLogger:
    """
    The central logging facility for the Adaptive Mind Framework.
    It standardizes event logging using UniversalEventSchema and
    provides a consistent interface for emitting telemetry events.
    """

    def __init__(self, component_name: str = "UnknownComponent"):
        """
        Initialize the CoreLogger for a specific component.

        Args:
            component_name: Name of the component using this logger
        """
        self.component_name = component_name
        self.logger = logging.getLogger(f"adaptive_mind.{component_name}")
        self.event_count = 0

    def log_event(
        self,
        event_type: str,
        event_topic: str,
        payload: Dict[str, Any] = None,
        severity: str = "INFO",
        parent_event_id: Optional[str] = None,
    ) -> str:
        """
        Log a structured event using UniversalEventSchema.

        Args:
            event_type: Type of event (e.g., 'api.call.success')
            event_topic: Topic/stream for the event (e.g., 'api.call')
            payload: Event-specific data
            severity: Log severity level
            parent_event_id: Optional parent event ID

        Returns:
            event_id: Unique ID of the logged event
        """
        try:
            # Create structured event
            event = UniversalEventSchema(
                event_type=event_type,
                event_topic=event_topic,
                event_source=self.component_name,
                severity=severity,
                payload=payload or {},
                parent_event_id=parent_event_id,
            )

            # Log the event
            log_message = f"[{event.event_type}] {event.payload}"

            if severity == "DEBUG":
                self.logger.debug(log_message)
            elif severity == "INFO":
                self.logger.info(log_message)
            elif severity == "WARNING":
                self.logger.warning(log_message)
            elif severity == "ERROR":
                self.logger.error(log_message)
            elif severity == "CRITICAL":
                self.logger.critical(log_message)
            else:
                self.logger.info(log_message)

            self.event_count += 1
            return event.event_id

        except Exception as e:
            self.logger.error(f"Failed to log structured event: {e}")
            return str(uuid.uuid4())

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        return self.log_event(
            "debug.message",
            "system.log",
            {"message": message, **kwargs},
            "DEBUG",
        )

    def info(self, message: str, **kwargs):
        """Log info message"""
        return self.log_event(
            "info.message",
            "system.log",
            {"message": message, **kwargs},
            "INFO",
        )

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        return self.log_event(
            "warning.message",
            "system.log",
            {"message": message, **kwargs},
            "WARNING",
        )

    def error(self, message: str, **kwargs):
        """Log error message"""
        return self.log_event(
            "error.message",
            "system.log",
            {"message": message, **kwargs},
            "ERROR",
        )

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        return self.log_event(
            "critical.message",
            "system.log",
            {"message": message, **kwargs},
            "CRITICAL",
        )

    # Add this method to your CoreLogger class in 01_Framework_Core/telemetry/core_logger.py

    def log(self, event_schema: "UniversalEventSchema") -> str:
        """
        Log a UniversalEventSchema directly.
        This method is called by BiasLedger and other components.

        Args:
            event_schema: UniversalEventSchema instance to log

        Returns:
            event_id: Unique ID of the logged event
        """
        try:
            # Extract event details from the schema
            if hasattr(event_schema, 'model_dump'):
                # If it's a Pydantic model, convert to dict
                event_dict = event_schema.model_dump()
            elif isinstance(event_schema, dict):
                # If it's already a dict, use it directly
                event_dict = event_schema
            else:
                # If it's an object with attributes, extract them
                event_dict = {
                    'event_type': getattr(event_schema, 'event_type', 'unknown.event'),
                    'event_topic': getattr(event_schema, 'event_topic', 'unknown.topic'),
                    'event_source': getattr(event_schema, 'event_source', 'unknown.source'),
                    'severity': getattr(event_schema, 'severity', 'INFO'),
                    'payload': getattr(event_schema, 'payload', {}),
                    'parent_event_id': getattr(event_schema, 'parent_event_id', None),
                }

            # Use the existing log_event method
            return self.log_event(
                event_type=event_dict.get('event_type', 'unknown.event'),
                event_topic=event_dict.get('event_topic', 'unknown.topic'),
                payload=event_dict.get('payload', {}),
                severity=event_dict.get('severity', 'INFO'),
                parent_event_id=event_dict.get('parent_event_id')
            )

        except Exception as e:
            self.logger.error(f"Failed to log UniversalEventSchema: {e}")
            return str(uuid.uuid4())


# Global logger instance
core_logger = CoreLogger("CoreFramework")


# Convenience functions for direct use
def log_structured_event(
    event_type: str,
    event_topic: str,
    payload: Dict[str, Any] = None,
    severity: str = "INFO",
    source: str = "Unknown",
) -> str:
    """Log a structured event directly"""
    logger = CoreLogger(source)
    return logger.log_event(event_type, event_topic, payload, severity)


def log_api_call(
    provider: str,
    model: str,
    success: bool,
    response_time_ms: float,
    cost_usd: float = 0.0,
    error: str = None,
) -> str:
    """Log an API call event"""
    event_type = "api.call.success" if success else "api.call.failure"
    payload = {
        "provider": provider,
        "model": model,
        "success": success,
        "response_time_ms": response_time_ms,
        "cost_usd": cost_usd,
    }

    if error:
        payload["error"] = error

    return log_structured_event(
        event_type,
        "api.call",
        payload,
        "INFO" if success else "ERROR",
        "APIHandler",
    )


def log_failover_event(
    from_provider: str,
    to_provider: str,
    reason: str,
    context_preserved: bool = True,
) -> str:
    """Log a failover event"""
    payload = {
        "from_provider": from_provider,
        "to_provider": to_provider,
        "reason": reason,
        "context_preserved": context_preserved,
    }

    return log_structured_event(
        "provider.failover",
        "system.resilience",
        payload,
        "WARNING",
        "FailoverEngine",
    )


def log_bias_event(
    bias_type: str, provider: str, confidence: float, description: str
) -> str:
    """Log a bias detection event"""
    payload = {
        "bias_type": bias_type,
        "provider": provider,
        "confidence": confidence,
        "description": description,
    }

    return log_structured_event(
        "bias.detected", "bias.ledger", payload, "WARNING", "BiasLedger"
    )


# Export the main logger for use throughout the framework
__all__ = [
    "CoreLogger",
    "core_logger",
    "UniversalEventSchema",
    "log_structured_event",
    "log_api_call",
    "log_failover_event",
    "log_bias_event",
]
