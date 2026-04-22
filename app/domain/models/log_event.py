from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class LogEvent:
    timestamp: datetime
    severity: str
    service: str
    message: str
    resource_type: str | None = None
    resource_labels: dict[str, str] = field(default_factory=dict)
    trace_id: str | None = None
    span_id: str | None = None
    labels: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def ensure_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
