from typing import Any, Literal

from pydantic import BaseModel, Field


class RawLogRecord(BaseModel):
    timestamp: str | None = None
    severity: str | None = None
    textPayload: str | None = None
    jsonPayload: dict[str, Any] | None = None
    resource: dict[str, Any] | None = None
    labels: dict[str, str] | None = None
    trace: str | None = None
    spanId: str | None = None


class AnalyzeRequest(BaseModel):
    source: Literal["gcp_logging", "raw_text", "jsonl"] = "gcp_logging"
    input_format: Literal["json", "jsonl", "text"] = "json"
    service: str = Field(..., min_length=1)
    window_size: str = "5m"
    severity_filter: list[str] = ["ERROR", "CRITICAL"]
    logs: list[RawLogRecord | str]
