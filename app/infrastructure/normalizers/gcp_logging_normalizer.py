from datetime import datetime, timezone

from app.api.schemas.request import RawLogRecord
from app.domain.models.log_event import LogEvent


class GCPLoggingNormalizer:
    def normalize(self, payload: object, default_service: str) -> LogEvent:
        if not isinstance(payload, RawLogRecord):
            raise TypeError("GCPLoggingNormalizer expects RawLogRecord payloads")

        raw = payload.model_dump(exclude_none=True)
        resource = payload.resource or {}
        resource_labels = {
            str(key): str(value)
            for key, value in (resource.get("labels") or {}).items()
        }

        service = resource_labels.get("service_name") or default_service
        message = self._extract_message(payload)
        timestamp = self._parse_timestamp(payload.timestamp)

        return LogEvent(
            timestamp=timestamp,
            severity=(payload.severity or "DEFAULT").upper(),
            service=service,
            message=message,
            resource_type=resource.get("type"),
            resource_labels=resource_labels,
            trace_id=payload.trace,
            span_id=payload.spanId,
            labels=payload.labels or {},
            raw=raw,
        )

    @staticmethod
    def _extract_message(payload: RawLogRecord) -> str:
        if payload.textPayload:
            return payload.textPayload
        if payload.jsonPayload:
            if "message" in payload.jsonPayload:
                return str(payload.jsonPayload["message"])
            return str(payload.jsonPayload)
        return ""

    @staticmethod
    def _parse_timestamp(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)

        candidate = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(candidate)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
