from datetime import datetime, timezone
import re

from app.domain.models.log_event import LogEvent


class TextNormalizer:
    _timestamp_prefix = re.compile(
        r"^(?P<ts>\d{4}-\d{2}-\d{2}[T ][0-9:\.\+\-Z]+)\s+(?P<rest>.*)$"
    )

    def normalize(self, payload: object, default_service: str) -> LogEvent:
        if not isinstance(payload, str):
            raise TypeError("TextNormalizer expects string payloads")

        timestamp, message = self._extract_timestamp(payload)
        severity = self._extract_severity(message)

        return LogEvent(
            timestamp=timestamp,
            severity=severity,
            service=default_service,
            message=message,
            raw={"message": payload},
        )

    def _extract_timestamp(self, payload: str) -> tuple[datetime, str]:
        match = self._timestamp_prefix.match(payload.strip())
        if not match:
            return datetime.now(timezone.utc), payload

        candidate = match.group("ts").replace(" ", "T").replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            return datetime.now(timezone.utc), payload

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return parsed, match.group("rest")

    @staticmethod
    def _extract_severity(message: str) -> str:
        upper = message.upper()
        if "CRITICAL" in upper:
            return "CRITICAL"
        if "ERROR" in upper or "EXCEPTION" in upper:
            return "ERROR"
        if "WARN" in upper:
            return "WARNING"
        return "INFO"
