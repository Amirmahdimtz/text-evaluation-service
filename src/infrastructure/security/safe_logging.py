"""Allowlisted event-only JSON logs; caller messages and exception text are suppressed."""

import json
import logging
import re
from datetime import datetime, timezone

_ALLOWED_EVENTS = frozenset({"APP_START", "APP_STOP", "REQUEST_FAILED", "CONFIG_ERROR", "AUTH_DENIED"})
_CORRELATION = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class SafeFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "safe_event", None)
        cid = getattr(record, "correlation_id", None)
        if event not in _ALLOWED_EVENTS:
            event = "UNCLASSIFIED_EVENT"
        if not isinstance(cid, str) or not _CORRELATION.fullmatch(cid):
            cid = None
        return json.dumps({
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "event_code": event,
            "correlation_id": cid,
        }, separators=(",", ":"))


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("text_evaluation_service")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(SafeFormatter())
        logger.addHandler(handler)
    return logger


def log_event(logger: logging.Logger, event_code: str, correlation_id: str | None = None) -> None:
    logger.info("safe_event", extra={"safe_event": event_code, "correlation_id": correlation_id})
