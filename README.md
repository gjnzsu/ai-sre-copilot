# Log Anomaly Agent

Log Anomaly Agent is a FastAPI service that detects short-term spikes in error logs and returns grouped anomaly windows with top failure patterns. It is designed for SRE and platform engineering workflows where fast incident triage matters more than full log search or storage.

## What It Does

- Accepts a batch of logs for a single service
- Normalizes supported log formats
- Filters logs by severity
- Detects anomalous spikes using a robust statistical baseline
- Clusters dominant message patterns
- Returns structured anomaly windows for downstream tooling or human triage

## Architecture

The architecture diagram below shows the main runtime boundaries and request-processing pipeline.

![Log Anomaly Agent architecture](docs/architecture/log-anomaly-agent-architecture.drawio.svg)

The editable source diagram is available at [docs/architecture/log-anomaly-agent-architecture.drawio](/abs/path/c:/SourceCode/ai-sre-copilot/docs/architecture/log-anomaly-agent-architecture.drawio:1).

## API Endpoints

### `GET /health`

Returns a simple health response:

```json
{
  "status": "ok",
  "env": "dev"
}
```

### `POST /v1/log-anomaly/analyze`

Analyzes a batch of logs and returns anomaly windows.

Example request:

```json
{
  "source": "gcp_logging",
  "input_format": "json",
  "service": "checkout-api",
  "window_size": "1m",
  "severity_filter": ["ERROR", "CRITICAL"],
  "logs": [
    {
      "timestamp": "2026-04-23T10:11:00Z",
      "severity": "ERROR",
      "resource": {
        "type": "cloud_run_revision",
        "labels": {
          "service_name": "checkout-api"
        }
      },
      "textPayload": "Redis connection timeout after 2500ms"
    }
  ]
}
```

Example response:

```json
{
  "source": "gcp_logging",
  "service": "checkout-api",
  "anomaly_windows": [
    {
      "start_time": "2026-04-23T10:11:00+00:00",
      "end_time": "2026-04-23T10:12:00+00:00",
      "error_count": 30,
      "baseline_error_count": 5,
      "spike_ratio": 6.0,
      "anomaly_score": 1.0,
      "top_patterns": [
        {
          "pattern": "redis connection timeout after <duration>",
          "count": 30,
          "examples": [
            "Redis connection timeout after 2500ms"
          ]
        }
      ],
      "suspicious_snippets": [
        "Redis connection timeout after 2500ms"
      ],
      "summary": null
    }
  ]
}
```

## Supported Input Modes

The request schema supports:

- `source = "gcp_logging"`
- `source = "raw_text"`
- `source = "jsonl"`

The current implementation is strongest for `gcp_logging` batches and simple text normalization.

## Configuration

Environment variables are loaded through `app.config.settings.Settings`.

Common settings:

- `APP_ENV`
- `PORT`
- `WINDOW_SIZE`
- `MIN_ERROR_COUNT`
- `MIN_SPIKE_RATIO`
- `ROBUST_Z_THRESHOLD`
- `ENABLE_LLM_SUMMARY`
- `OPENAI_API_KEY`

Current Kubernetes defaults are defined in [k8s/configmap.yaml](/abs/path/c:/SourceCode/ai-sre-copilot/k8s/configmap.yaml:1) and [k8s/secret.yaml](/abs/path/c:/SourceCode/ai-sre-copilot/k8s/secret.yaml:1).

## Local Development

Requirements:

- Python 3.11+
- `uv`

Install dependencies:

```powershell
uv sync --extra dev
```

Run the API locally:

```powershell
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## Quality Checks

Run lint plus tests:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\quality-check.ps1
```

Individual commands:

```powershell
uvx ruff check app tests
uv run pytest
```

## Docker

Build the container image:

```powershell
docker build -t log-anomaly-agent:local .
```

Run the container locally:

```powershell
docker run --rm -p 8080:8080 log-anomaly-agent:local
```

## Kubernetes Deployment

This repo includes manifests under [k8s](/abs/path/c:/SourceCode/ai-sre-copilot/k8s:1).

Apply them:

```powershell
kubectl apply -f k8s\namespace.yaml
kubectl apply -f k8s\configmap.yaml -f k8s\secret.yaml -f k8s\deployment.yaml -f k8s\service.yaml
```

Current deployment image:

```text
gcr.io/gen-lang-client-0896070179/log-anomaly-agent:latest
```

Check rollout:

```powershell
kubectl rollout status deployment/log-anomaly-agent -n ai-sre
kubectl get pods -n ai-sre
```

## Project Structure

```text
app/
  api/             FastAPI routes and request/response schemas
  application/     Orchestration service for batch analysis
  config/          Runtime settings
  domain/          Core models and ports
  infrastructure/  Detection, normalization, and pattern mining implementations
tests/
  integration/     API and health check tests
k8s/               Kubernetes manifests
scripts/           Local developer scripts
```

## Current Limitations

- The service is request/batch driven, not streaming.
- It does not store logs or anomaly history.
- It does not currently generate LLM-based summaries, even though the config flag exists.
- It is best suited to internal service-to-service or workflow integration today.
