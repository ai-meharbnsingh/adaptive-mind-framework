# telemetry/core_logger.py

import logging
import json
import os
import threading
import time
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any


class UniversalEventSchema(BaseModel):
    event_type: str = Field(..., description="The type of event being logged (e.g., 'API_CALL', 'FAILOVER').")
    event_source: str = Field(..., description="The component or module that generated the event.")
    timestamp_utc: str = Field(..., description="ISO 8601 formatted UTC timestamp.")
    severity: str = Field(..., description="Log severity level (e.g., 'INFO', 'WARNING', 'ERROR').")
    payload: Dict[str, Any] = Field(..., description="A flexible dictionary for event-specific data.")

    def to_dict(self):
        return self.model_dump()


class JsonFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        """
        Custom time formatter to handle milliseconds correctly and produce ISO 8601 format.
        """
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            # For compatibility if a simple format is passed, but we'll override for ISO
            s = ct.strftime(datefmt)
        else:
            s = ct.isoformat()

        # Ensure the format is exactly what we want: ISO 8601 with milliseconds and Z
        return f"{s[:-3]}Z"

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "level": record.levelname,
            "name": record.name,
        }

        # Prefer the pre-formatted, highly accurate timestamp from the event schema
        if hasattr(record, 'event_data') and 'timestamp_utc' in record.event_data:
            log_record["timestamp_utc"] = record.event_data['timestamp_utc']
        else:
            log_record["timestamp_utc"] = self.formatTime(record)

        if hasattr(record, 'event_data'):
            log_record.update(record.event_data)
        else:
            log_record['message'] = record.getMessage()

        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(log_record, default=str)


class AdaptiveMindLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        self.propagate = False

        self.formatter = JsonFormatter()

        if not self.handlers:
            self.console_handler = logging.StreamHandler()
            self.console_handler.setFormatter(self.formatter)
            self.addHandler(self.console_handler)

    def log(self, event_or_message, **kwargs):
        if isinstance(event_or_message, UniversalEventSchema):
            event = event_or_message
            log_level = getattr(logging, event.severity.upper(), logging.INFO)
            super().log(log_level, event.event_type, extra={'event_data': event.model_dump()})
        else:
            # Fallback for any other call, ensuring it doesn't crash
            super().log(logging.INFO, str(event_or_message))


class CoreLoggerSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    logging.setLoggerClass(AdaptiveMindLogger)
                    cls._instance = logging.getLogger("AdaptiveMind")
                    cls._instance.setLevel(logging.DEBUG)
        return cls._instance


core_logger = CoreLoggerSingleton()