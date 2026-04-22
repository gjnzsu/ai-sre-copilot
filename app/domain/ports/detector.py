from typing import Protocol

from app.domain.models.anomaly_window import AnomalyWindow
from app.domain.models.log_event import LogEvent


class Detector(Protocol):
    def detect(self, events: list[LogEvent], window_size: str) -> list[AnomalyWindow]:
        ...
