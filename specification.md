# WP-006 — Add `notify-obs` Deployment Event Step

**Type:** feat / observability
**Depends on:** WP-001 (init), WP-005 (upload-defectdojo)
**Branch:** `feature/wp-006-notify-obs`

---

## 1. Problem

The v0.2 pipeline design requires a `notify-obs` step that emits a structured deployment event to uFawkesObs (via the OTEL collector). This event enables DORA deployment frequency and change lead time metrics by recording when a pipeline successfully completes on `main`.

Currently, no such step exists. The pipeline ends after `upload-defectdojo` with no deployment event emission.

---

## 2. Requirements

### Functional

| # | Requirement | Rationale |
|---|---|---|
| F1 | Step named `notify-obs` uses image `curlimages/curl:latest` | Minimal curl image for HTTP POST |
| F2 | `notify-obs` POSTs JSON to `${OTEL_ENDPOINT}/v1/traces` (or deployment event endpoint) | Emits deployment event to observability backend |
| F3 | Event payload includes: `service.name`, `deployment.environment`, `deployment.version`, `deployment.status`, `git.commit.sha`, `git.branch`, `pipeline.duration_ms` | Standard DORA/OTEL deployment event attributes |
| F4 | `notify-obs` has `when: branch: main` condition | Only production deployments (main branch) generate deployment events |
| F5 | Step is non-blocking (exit code 0 always) | Observability failure must not fail the deployment |
| F6 | Uses secrets: `OTEL_ENDPOINT` from_secret, optional `OTEL_HEADERS` from_secret | Endpoint and auth configured via secrets |
| F7 | DORA structured logging at start and end of step | Consistent with all pipeline steps |

### Non-Functional

| # | Requirement | Rationale |
|---|---|---|
| NF1 | Structured JSON logging (DORA format) | Consistent with all other pipeline steps |
| NF2 | Timeout ≤ 10 seconds | Observability call must be fast and non-blocking |
| NF3 | No hard dependency on uFawkesObs being reachable | Step must not fail pipeline if observability is down |

---

## 3. Acceptance Criteria

1. Step `notify-obs` exists in `.woodpecker.yml` with image `curlimages/curl:latest`
2. `notify-obs` has `when:` condition with `branch: main`
3. Step uses `environment.OTEL_ENDPOINT.from_secret: otel_endpoint`
4. Step uses `environment.OTEL_HEADERS.from_secret: otel_headers` (optional, guarded)
5. Commands POST JSON deployment event to `${OTEL_ENDPOINT}/v1/traces` (or correct endpoint)
6. Event payload includes required DORA attributes (service.name, deployment.environment, deployment.version, deployment.status, git.commit.sha, git.branch, pipeline.duration_ms)
7. Step is non-blocking: uses `|| true` or equivalent to always exit 0
8. Comment explaining non-blocking nature exists
9. DORA structured JSON logging present at step start and end
10. `tests/unit/test_woodpecker_yml.py` updated with `TestNotifyObsStep` class (minimum 10 test methods)
11. `pytest tests/` passes with zero failures

---

## 4. Dependencies

- **WP-001** (init): artifact directories must exist
- **WP-005** (upload-defectdojo): notify-obs runs after security scan ingestion completes

---

## 5. Out of Scope

- uFawkesObs infrastructure deployment (separate repo: uFawkesObs)
- Deployment event schema versioning (uses current OTEL standard)
- Retry logic for failed observability calls (v0.3 item)

---

## 6. Environment Variables

| Variable | Source | Required | Notes |
|---|---|---|---|
| `OTEL_ENDPOINT` | from_secret: otel_endpoint | Yes | e.g., `http://otel-collector:4318` |
| `OTEL_HEADERS` | from_secret: otel_headers | No | Optional auth headers for OTEL collector |
