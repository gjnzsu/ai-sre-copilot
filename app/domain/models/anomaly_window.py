from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AnomalyWindow:
    start_time: datetime
    end_time: datetime
    error_count: int
    baseline_error_count: int
    spike_ratio: float
    anomaly_score: float
