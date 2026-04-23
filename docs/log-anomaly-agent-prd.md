# Log Anomaly Agent PRD

## 1. Executive Summary

Log Anomaly Agent is a lightweight API service for SREs and platform engineers that detects short-term spikes in error logs, clusters the most common suspicious patterns, and returns a structured anomaly summary for a single service at a time. The goal is to reduce time-to-triage during incident response and make noisy log streams easier to interpret without requiring engineers to manually scan raw events.

## 2. Problem Statement

### Who has this problem?

Primary users are SREs and platform engineers responsible for production services and incident response.

Secondary users are application developers investigating regressions or service instability in their own workloads.

### What is the problem?

When error volume spikes, responders often need to manually inspect large volumes of logs to determine whether there is a real anomaly, which service is affected, and which failure patterns dominate the event stream. This is slow, repetitive, and brittle under time pressure.

### Why is it painful?

- Engineers lose valuable incident response time scanning raw logs.
- High-volume error bursts can hide the most actionable pattern.
- Manual triage makes it harder to separate a real spike from expected background noise.
- Repeated ad hoc investigation creates inconsistent operational behavior across teams.

### Evidence

- The service design already centers on error spike detection, severity filtering, and pattern clustering, which indicates the operational need is triage speed rather than log storage or search.
- The current API returns anomaly windows, baseline counts, spike ratios, and top patterns, which aligns with incident investigation workflows.
- Existing deployment and health-check setup show the intent is to run this as a production-facing internal service.

## 3. Target Users and Personas

### Primary Persona: Platform SRE

- Owns production reliability for multiple services.
- Needs fast signal extraction from noisy operational data.
- Cares about confidence, clear summaries, and low-latency triage tooling.
- Uses logs to decide whether to escalate, roll back, or dig deeper.

### Secondary Persona: Service Owner Developer

- Owns one or a small set of application services.
- Needs a simple way to inspect whether recent logs indicate a meaningful issue.
- Values clear patterns and example snippets more than advanced statistical detail.

## 4. Strategic Context

### Why now?

- As service fleets grow, manual log triage becomes increasingly expensive.
- Teams need a simple building block that can be embedded into broader observability or copilot workflows.
- The current implementation provides a good foundation for production hardening and future automation.

### Business and Operational Value

- Reduce mean time to detect and understand an incident.
- Improve consistency of incident triage across services.
- Create a reusable API for future alerting, summarization, and remediation workflows.

## 5. Solution Overview

Log Anomaly Agent provides an HTTP API that accepts a batch of logs for a target service, normalizes them, filters them by severity, groups them into windows, identifies spike conditions using a robust statistical detector, and returns the anomaly windows with clustered patterns and example snippets.

### Current Product Behavior

- Supports `gcp_logging`, `raw_text`, and `jsonl` style request sources.
- Filters logs by severity before anomaly detection.
- Detects spikes using rolling history, median baseline, median absolute deviation, and configurable thresholds.
- Clusters similar messages into templates and returns top patterns.
- Exposes `/health` for readiness and liveness checks.

### Key API Behavior

- Endpoint: `POST /v1/log-anomaly/analyze`
- Health: `GET /health`
- Input: service name, window size, severity filter, and logs
- Output: anomaly windows with counts, ratios, patterns, and snippets

## 6. Success Metrics

### Primary Metric

- Time to identify the dominant failure pattern after a spike begins

### Secondary Metrics

- Percentage of log batches that produce at least one actionable anomaly window
- Median API response time for typical batch sizes
- Reduction in manual log review time during incident triage
- Adoption by internal engineering teams or workflows

### Initial Targets

- Healthy requests succeed reliably with clear anomaly summaries
- Triage users can identify top patterns from one API response without manually reviewing the full batch
- Service remains deployable and observable in Kubernetes

## 7. User Stories and Requirements

### Epic Hypothesis

If SREs can submit a batch of recent service logs and immediately receive anomaly windows with top clustered patterns, they will triage production incidents faster and with less manual log scanning.

### User Story 1

As an SRE, I want to submit a batch of recent logs for one service so that I can quickly determine whether there is a meaningful error spike.

#### Acceptance Criteria

- The API accepts a request with `service`, `logs`, `source`, and `window_size`.
- The response includes zero or more anomaly windows.
- Each anomaly window includes `error_count`, `baseline_error_count`, `spike_ratio`, and `anomaly_score`.

### User Story 2

As an SRE, I want the result to include dominant patterns and example snippets so that I can understand what kind of failure is occurring.

#### Acceptance Criteria

- Each anomaly window includes `top_patterns`.
- Each pattern includes a normalized template, occurrence count, and example messages.
- Each anomaly window includes `suspicious_snippets` for quick inspection.

### User Story 3

As a platform engineer, I want the service to be deployable in Kubernetes with health probes so that it can run as part of production tooling.

#### Acceptance Criteria

- The service exposes `GET /health`.
- Kubernetes readiness and liveness probes use the health endpoint.
- Runtime behavior can be configured through environment variables.

### Constraints

- Current implementation is batch-oriented, not streaming.
- Current implementation does not persist data.
- Current implementation does not perform alert routing or remediation.
- `ENABLE_LLM_SUMMARY` exists in configuration but summary generation is not yet implemented end to end.

## 8. Out of Scope

- Full log ingestion pipeline ownership
- Long-term log storage or indexing
- Multi-tenant UI dashboards
- Alert delivery integrations such as Slack, PagerDuty, or email
- Automatic remediation or runbook execution
- Advanced ML model training or online learning

## 9. Dependencies and Risks

### Dependencies

- FastAPI-based service runtime
- Kubernetes deployment environment
- Upstream log producers that provide well-formed batches

### Risks

- Sparse or irregular log streams may reduce anomaly quality.
- Mixed-format logs may produce lower-quality normalization.
- Large payloads may affect latency if request sizes grow substantially.
- Current tests are narrow and focus on the happy path.

### Mitigations

- Keep configuration thresholds adjustable by environment.
- Expand tests around sparse data, mixed severities, and alternate source formats.
- Keep deployment health checks simple and explicit.

## 10. Open Questions

- Should the service eventually consume logs directly from GCP or remain batch-input only?
- Should anomaly summaries include a human-readable synthesized explanation?
- What request volume and payload size should define the production SLO?
- Should the product evolve into a standalone service, a sidecar tool, or part of a broader observability platform?

