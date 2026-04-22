from collections import defaultdict
import hashlib
import re

from app.domain.models.log_event import LogEvent
from app.domain.models.pattern_cluster import PatternCluster


class TemplatePatternMiner:
    _uuid_pattern = re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    )
    _number_pattern = re.compile(r"\b\d+\b")
    _ip_pattern = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
    _duration_pattern = re.compile(r"\b\d+(?:ms|s|m)\b")

    def mine(self, events: list[LogEvent]) -> list[PatternCluster]:
        groups: dict[str, list[str]] = defaultdict(list)
        for event in events:
            template = self._canonicalize(event.message)
            groups[template].append(event.message)

        clusters = [
            PatternCluster(
                pattern_id=self._pattern_id(template),
                pattern=template,
                count=len(messages),
                examples=messages[:3],
            )
            for template, messages in groups.items()
        ]
        return sorted(clusters, key=lambda item: item.count, reverse=True)

    def _canonicalize(self, message: str) -> str:
        canonical = message.lower()
        canonical = self._uuid_pattern.sub("<uuid>", canonical)
        canonical = self._ip_pattern.sub("<ip>", canonical)
        canonical = self._duration_pattern.sub("<duration>", canonical)
        canonical = self._number_pattern.sub("<num>", canonical)
        canonical = re.sub(r"\s+", " ", canonical).strip()
        return canonical

    @staticmethod
    def _pattern_id(pattern: str) -> str:
        digest = hashlib.md5(pattern.encode("utf-8"), usedforsecurity=False).hexdigest()
        return f"ptn_{digest[:12]}"
