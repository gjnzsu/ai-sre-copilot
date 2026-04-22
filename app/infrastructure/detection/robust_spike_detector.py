from collections import Counter
from datetime import datetime, timedelta, timezone
from statistics import median

from app.domain.models.anomaly_window import AnomalyWindow
from app.domain.models.log_event import LogEvent


class RobustSpikeDetector:
    def __init__(
        self,
        default_window_size: str = "5m",
        min_error_count: int = 20,
        min_spike_ratio: float = 3.0,
        robust_z_threshold: float = 3.5,
    ) -> None:
        self._default_window_size = default_window_size
        self._min_error_count = min_error_count
        self._min_spike_ratio = min_spike_ratio
        self._robust_z_threshold = robust_z_threshold

    def detect(self, events: list[LogEvent], window_size: str) -> list[AnomalyWindow]:
        if not events:
            return []

        delta = self._parse_window_size(window_size or self._default_window_size)
        counters = self._group_by_window(events, delta)
        ordered_keys = sorted(counters.keys())
        windows: list[AnomalyWindow] = []

        for index, window_start in enumerate(ordered_keys):
            current_count = counters[window_start]
            history_keys = ordered_keys[max(0, index - 12):index]
            history = [counters[key] for key in history_keys]
            if len(history) < 3:
                continue

            baseline = median(history)
            deviations = [abs(value - baseline) for value in history]
            mad = median(deviations) or 1.0
            robust_z = 0.6745 * (current_count - baseline) / mad
            spike_ratio = current_count / max(baseline, 1)

            if (
                current_count >= self._min_error_count
                and spike_ratio >= self._min_spike_ratio
                and robust_z >= self._robust_z_threshold
            ):
                windows.append(
                    AnomalyWindow(
                        start_time=window_start,
                        end_time=window_start + delta,
                        error_count=current_count,
                        baseline_error_count=int(baseline),
                        spike_ratio=round(spike_ratio, 2),
                        anomaly_score=round(min(1.0, robust_z / 10.0), 2),
                    )
                )
        return windows

    @staticmethod
    def _parse_window_size(value: str) -> timedelta:
        unit = value[-1]
        amount = int(value[:-1])
        if unit == "m":
            return timedelta(minutes=amount)
        if unit == "h":
            return timedelta(hours=amount)
        raise ValueError(f"Unsupported window size: {value}")

    @staticmethod
    def _group_by_window(events: list[LogEvent], delta: timedelta) -> Counter[datetime]:
        counts: Counter[datetime] = Counter()
        for event in events:
            timestamp = event.timestamp.astimezone(timezone.utc)
            window_start = RobustSpikeDetector._floor_time(timestamp, delta)
            counts[window_start] += 1
        return counts

    @staticmethod
    def _floor_time(value: datetime, delta: timedelta) -> datetime:
        epoch = int(value.timestamp())
        bucket = int(delta.total_seconds())
        floored = epoch - (epoch % bucket)
        return datetime.fromtimestamp(floored, tz=timezone.utc)
