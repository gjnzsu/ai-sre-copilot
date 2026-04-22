from fastapi.testclient import TestClient

from app.main import app


def test_analyze_returns_anomaly_windows_for_spike() -> None:
    client = TestClient(app)
    logs = []

    for minute in range(12):
        count = 5
        if minute == 11:
            count = 30
        for index in range(count):
            logs.append(
                {
                    "timestamp": f"2026-04-23T10:{minute:02d}:{index:02d}Z",
                    "severity": "ERROR",
                    "resource": {
                        "type": "cloud_run_revision",
                        "labels": {"service_name": "checkout-api"},
                    },
                    "textPayload": f"Redis connection timeout after {2000 + index}ms",
                }
            )

    response = client.post(
        "/v1/log-anomaly/analyze",
        json={
            "source": "gcp_logging",
            "input_format": "json",
            "service": "checkout-api",
            "window_size": "1m",
            "severity_filter": ["ERROR", "CRITICAL"],
            "logs": logs,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "checkout-api"
    assert len(payload["anomaly_windows"]) == 1
    window = payload["anomaly_windows"][0]
    assert window["error_count"] == 30
    assert window["baseline_error_count"] == 5
    assert window["top_patterns"][0]["pattern"] == "redis connection timeout after <duration>"
