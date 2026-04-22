from typing import Protocol

from app.domain.models.log_event import LogEvent


class Normalizer(Protocol):
    def normalize(self, payload: object, default_service: str) -> LogEvent:
        ...
