from collections.abc import Iterable

from app.api.schemas.request import AnalyzeRequest, RawLogRecord
from app.api.schemas.response import AnalyzeResponse, AnomalyWindowResponse, PatternSummary
from app.domain.models.anomaly_window import AnomalyWindow
from app.domain.models.log_event import LogEvent
from app.domain.ports.detector import Detector
from app.domain.ports.normalizer import Normalizer
from app.domain.ports.pattern_miner import PatternMiner


class AnalyzeBatchService:
    def __init__(
        self,
        gcp_normalizer: Normalizer,
        text_normalizer: Normalizer,
        detector: Detector,
        pattern_miner: PatternMiner,
    ) -> None:
        self._gcp_normalizer = gcp_normalizer
        self._text_normalizer = text_normalizer
        self._detector = detector
        self._pattern_miner = pattern_miner

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        normalized = list(self._normalize_logs(request))
        filtered = [
            event
            for event in normalized
            if event.severity.upper() in {level.upper() for level in request.severity_filter}
        ]
        windows = self._detector.detect(filtered, request.window_size)

        response_windows: list[AnomalyWindowResponse] = []
        for window in windows:
            window_events = self._events_for_window(filtered, window)
            patterns = self._pattern_miner.mine(window_events)
            response_windows.append(
                AnomalyWindowResponse(
                    start_time=window.start_time.isoformat(),
                    end_time=window.end_time.isoformat(),
                    error_count=window.error_count,
                    baseline_error_count=window.baseline_error_count,
                    spike_ratio=window.spike_ratio,
                    anomaly_score=window.anomaly_score,
                    top_patterns=[
                        PatternSummary(
                            pattern=pattern.pattern,
                            count=pattern.count,
                            examples=pattern.examples,
                        )
                        for pattern in patterns
                    ],
                    suspicious_snippets=[
                        example for pattern in patterns[:3] for example in pattern.examples[:1]
                    ],
                )
            )

        return AnalyzeResponse(
            source=request.source,
            service=request.service,
            anomaly_windows=response_windows,
        )

    def _normalize_logs(self, request: AnalyzeRequest) -> Iterable[LogEvent]:
        if request.source == "gcp_logging":
            for item in request.logs:
                if isinstance(item, str):
                    continue
                yield self._gcp_normalizer.normalize(item, request.service)
            return

        for item in request.logs:
            if isinstance(item, str):
                yield self._text_normalizer.normalize(item, request.service)
            else:
                raw_text = self._record_to_text(item)
                yield self._text_normalizer.normalize(raw_text, request.service)

    @staticmethod
    def _record_to_text(item: RawLogRecord) -> str:
        if item.textPayload:
            return item.textPayload
        if item.jsonPayload and "message" in item.jsonPayload:
            return str(item.jsonPayload["message"])
        return str(item.model_dump(exclude_none=True))

    @staticmethod
    def _events_for_window(events: list[LogEvent], window: AnomalyWindow) -> list[LogEvent]:
        return [
            event
            for event in events
            if window.start_time <= event.timestamp < window.end_time
        ]
