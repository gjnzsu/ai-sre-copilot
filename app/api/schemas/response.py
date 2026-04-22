from pydantic import BaseModel, Field


class PatternSummary(BaseModel):
    pattern: str
    count: int
    examples: list[str]


class AnomalyWindowResponse(BaseModel):
    start_time: str
    end_time: str
    error_count: int
    baseline_error_count: int
    spike_ratio: float
    anomaly_score: float
    top_patterns: list[PatternSummary] = Field(default_factory=list)
    suspicious_snippets: list[str] = Field(default_factory=list)
    summary: str | None = None


class AnalyzeResponse(BaseModel):
    source: str
    service: str
    anomaly_windows: list[AnomalyWindowResponse] = Field(default_factory=list)
