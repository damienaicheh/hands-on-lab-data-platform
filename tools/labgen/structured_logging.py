"""Structured JSON logging setup used by the LabGen runtime."""

import json
import logging
import sys
from datetime import datetime, timezone

_RESERVED_LOG_RECORD_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class JsonLogFormatter(logging.Formatter):
    """Formats standard logging records as single-line JSON payloads."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert one log record into a JSON document string."""
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", "log"),
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_FIELDS or key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True, default=str)


def configure_structured_logger(level: int = logging.WARNING) -> logging.Logger:
    """Create and return the LabGen logger configured for JSON output."""
    logger = logging.getLogger("labgen")
    logger.handlers.clear()
    logger.setLevel(level)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)

    return logger
