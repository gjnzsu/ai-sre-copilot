from typing import Protocol

from app.domain.models.log_event import LogEvent
from app.domain.models.pattern_cluster import PatternCluster


class PatternMiner(Protocol):
    def mine(self, events: list[LogEvent]) -> list[PatternCluster]:
        ...
