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

## How To Use This Service

Use this service when you already have a batch of recent logs for one service and want a quick answer to: "Did error volume spike, and what error pattern should I investigate first?"

### 1. Start the API

For local development:

```powershell
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

For a containerized local run:

```powershell
docker build -t log-anomaly-agent:local .
docker run --rm -p 8080:8080 log-anomaly-agent:local
```

Check that the service is ready:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health | Select-Object -ExpandProperty Content
```

Expected response:

```json
{"status":"ok","env":"dev"}
```

### 2. Submit Logs For Analysis

Send a `POST` request to `/v1/log-anomaly/analyze` with a service name, window size, severity filter, and log batch.

PowerShell example:

```powershell
$body = @{
  source = "gcp_logging"
  input_format = "json"
  service = "checkout-api"
  window_size = "1m"
  severity_filter = @("ERROR", "CRITICAL")
  logs = @(
    @{
      timestamp = "2026-04-23T10:00:00Z"
      severity = "ERROR"
      resource = @{
        type = "cloud_run_revision"
        labels = @{
          service_name = "checkout-api"
        }
      }
      textPayload = "Redis connection timeout after 2500ms"
    }
  )
} | ConvertTo-Json -Depth 8

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8080/v1/log-anomaly/analyze" `
  -ContentType "application/json" `
  -Body $body
```

For meaningful spike detection, submit enough historical windows before the suspected spike. For example, if `window_size` is `1m`, include several minutes of baseline logs plus the current minute.

### 3. Interpret The Response

The most important response fields are:

- `anomaly_windows`: windows where the detector found a spike.
- `error_count`: number of matching severity logs in that window.
- `baseline_error_count`: median count from recent historical windows.
- `spike_ratio`: current count divided by the baseline.
- `anomaly_score`: normalized score from the robust z-score calculation.
- `top_patterns`: normalized error templates with counts and examples.
- `suspicious_snippets`: quick example messages to inspect first.

If `anomaly_windows` is empty, the batch did not cross the configured anomaly thresholds. That can mean the service is healthy, the log batch is too small, or the thresholds are too strict for the workload.

### 4. Tune For Your Workload

Start with the defaults, then tune based on service traffic:

- Increase `MIN_ERROR_COUNT` for high-volume services to avoid noisy alerts.
- Decrease `MIN_ERROR_COUNT` for low-volume services where a small burst is meaningful.
- Increase `MIN_SPIKE_RATIO` if expected traffic cycles create false positives.
- Lower `ROBUST_Z_THRESHOLD` if real spikes are being missed.
- Use a smaller `WINDOW_SIZE` for fast-moving incidents and a larger window for slower trends.

Recommended first production pattern:

- Run the service behind an internal API or workflow.
- Send one service's logs per request.
- Keep the first integration read-only and human-in-the-loop.
- Review `top_patterns` before wiring the output into alerting or automation.

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
