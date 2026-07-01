# WP-006 — Design: `notify-obs` Deployment Event Step

## 1. Architecture Overview

The `notify-obs` step is the final stage in the v0.2 pipeline, responsible for emitting a **deployment event** to the observability backend (uFawkesObs via OTEL Collector). This event enables DORA metrics calculation (deployment frequency, change lead time).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WOODPECKER PIPELINE (v0.2)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ init → secrets-scan → lint-yaml → lint-shell → validate-contract →          │
│ vuln-scan-fs → vuln-scan-image → upload-defectdojo → notify-obs             │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                       │
                                                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          uFawkesObs (OTEL Collector)                        │
│  Receives deployment event → enriches with trace context → stores in Loki   │
│  DORA measurement queries Loki for deployment frequency / lead time         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Component Design

### 2.1 Pipeline Step: `notify-obs`

| Property | Value |
|---|---|
| **Name** | `notify-obs` |
| **Image** | `curlimages/curl:latest` (pinned to latest — documented exception for scanner/curl images) |
| **When** | `branch: main` |
| **Secrets** | `OTEL_ENDPOINT.from_secret: otel_endpoint`<br>`OTEL_HEADERS.from_secret: otel_headers` (optional) |
| **Commands** | See §2.2 |
| **Exit Behavior** | Always exit 0 (non-blocking) |

### 2.2 Command Sequence

```bash
#!/usr/bin/env bash
set -euo pipefail

# DORA start log
echo '{"level":"info","event":"notify-obs:start","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","pipeline":"woodpecker","stage":"notify-obs"}'

# Build deployment event payload
DEPLOYMENT_EVENT=$(cat <<EOF
{
  "resourceSpans": [{
    "resource": {
      "attributes": [
        {"key": "service.name", "value": {"stringValue": "ufawkespipe"}},
        {"key": "deployment.environment", "value": {"stringValue": "production"}},
        {"key": "deployment.version", "value": {"stringValue": "${CI_COMMIT_SHA:0:7}"}},
        {"key": "deployment.status", "value": {"stringValue": "success"}}
      ]
    },
    "scopeSpans": [{
      "spans": [{
        "name": "deployment",
        "kind": "SPAN_KIND_INTERNAL",
        "startTimeUnixNano": "$(date -u +%s)000000000",
        "endTimeUnixNano": "$(date -u +%s)000000000",
        "attributes": [
          {"key": "git.commit.sha", "value": {"stringValue": "${CI_COMMIT_SHA}"}},
          {"key": "git.branch", "value": {"stringValue": "${CI_COMMIT_BRANCH}"}},
          {"key": "pipeline.duration_ms", "value": {"intValue": "${PIPELINE_DURATION_MS:-0}"}}
        ]
      }]
    }]
  }]
}
EOF
)

# POST to OTEL collector (non-blocking)
if [ -n "${OTEL_ENDPOINT:-}" ]; then
  curl -s -X POST "${OTEL_ENDPOINT}/v1/traces" \
    -H "Content-Type: application/json" \
    ${OTEL_HEADERS:+-H "${OTEL_HEADERS}"} \
    -d "${DEPLOYMENT_EVENT}" \
    -w "\nHTTP %{http_code}\n" \
    -o /dev/null || true
else
  echo '{"level":"warn","event":"notify-obs:skipped","reason":"OTEL_ENDPOINT not set","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'
fi

# DORA finish log
echo '{"level":"info","event":"notify-obs:end","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","pipeline":"woodpecker","stage":"notify-obs"}'
```

### 2.3 Woodpecker YAML Representation

```yaml
notify-obs:
  image: curlimages/curl:latest
  when:
    branch: main
  environment:
    OTEL_ENDPOINT:
      from_secret: otel_endpoint
    OTEL_HEADERS:
      from_secret: otel_headers
  commands:
    - |
      set -euo pipefail
      echo '{"level":"info","event":"notify-obs:start","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","pipeline":"woodpecker","stage":"notify-obs"}'
      DEPLOYMENT_EVENT=$(cat <<'EOF'
      {
        "resourceSpans": [{
          "resource": {
            "attributes": [
              {"key": "service.name", "value": {"stringValue": "ufawkespipe"}},
              {"key": "deployment.environment", "value": {"stringValue": "production"}},
              {"key": "deployment.version", "value": {"stringValue": "${CI_COMMIT_SHA:0:7}"}},
              {"key": "deployment.status", "value": {"stringValue": "success"}}
            ]
          },
          "scopeSpans": [{
            "spans": [{
              "name": "deployment",
              "kind": "SPAN_KIND_INTERNAL",
              "startTimeUnixNano": "$(date -u +%s)000000000",
              "endTimeUnixNano": "$(date -u +%s)000000000",
              "attributes": [
                {"key": "git.commit.sha", "value": {"stringValue": "${CI_COMMIT_SHA}"}},
                {"key": "git.branch", "value": {"stringValue": "${CI_COMMIT_BRANCH}"}},
                {"key": "pipeline.duration_ms", "value": {"intValue": "${PIPELINE_DURATION_MS:-0}"}}
              ]
            }]
          }]
        }]
      }
EOF'
      )
      if [ -n "${OTEL_ENDPOINT:-}" ]; then
        curl -s -X POST "${OTEL_ENDPOINT}/v1/traces" \
          -H "Content-Type: application/json" \
          ${OTEL_HEADERS:+-H "${OTEL_HEADERS}"} \
          -d "${DEPLOYMENT_EVENT}" \
          -w "\nHTTP %{http_code}\n" \
          -o /dev/null || true
      else
        echo '{"level":"warn","event":"notify-obs:skipped","reason":"OTEL_ENDPOINT not set","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'
      fi
      echo '{"level":"info","event":"notify-obs:end","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","pipeline":"woodpecker","stage":"notify-obs"}'
```

## 3. Data Flow

```
Woodpecker CI (main branch)
         │
         ▼
notify-obs step
         │
         ├─ Reads CI_COMMIT_SHA, CI_COMMIT_BRANCH from Woodpecker env
         ├─ Reads PIPELINE_DURATION_MS from previous step (or computes)
         ├─ Reads OTEL_ENDPOINT from secret
         ├─ Reads OTEL_HEADERS from secret (optional)
         │
         ▼
POST /v1/traces to OTEL Collector (HTTP)
         │
         ▼
uFawkesObs → Loki → DORA Measurement
```

## 4. Integration Points

| Interface | Provider | Consumer | Protocol |
|---|---|---|---|
| OTEL HTTP endpoint | uFawkesObs (OTEL Collector) | notify-obs | HTTP/JSON (OTLP HTTP) |
| Woodpecker secrets | Woodpecker server | notify-obs | `from_secret:` |
| CI env vars | Woodpecker runner | notify-obs | `CI_COMMIT_SHA`, `CI_COMMIT_BRANCH`, etc. |

## 5. Security

- No credentials in YAML — all via `from_secret:`
- `OTEL_HEADERS` optional (supports bearer tokens, API keys)
- Step runs only on `main` branch (production deployments only)
- Non-blocking: observability failure never fails deployment

## 6. Error Handling

| Scenario | Behavior |
|---|---|
| OTEL_ENDPOINT secret not set | Log warning, skip POST, exit 0 |
| Network timeout / unreachable | curl OR true — log warning, exit 0 |
| HTTP 4xx/5xx response | Log response code, exit 0 |
| Malformed JSON payload | Independent of shell expansion; exit 0 |

## 7. Testing Strategy

### Unit Tests (test_woodpecker_yml.py)

- `TestNotifyObsStep::test_step_exists`
- `TestNotifyObsStep::test_uses_curl_image`
- `TestNotifyObsStep::test_branch_main_only`
- `TestNotifyObsStep::test_has_otel_endpoint_secret`
- `TestNotifyObsStep::test_has_otel_headers_secret_optional`
- `TestNotifyObsStep::test_commands_include_dora_start_log`
- `TestNotifyObsStep::test_commands_include_dora_end_log`
- `TestNotifyObsStep::test_commands_post_to_otel_endpoint`
- `TestNotifyObsStep::test_non_blocking_curl_or_true`
- `TestNotifyObsStep::test_payload_includes_required_attributes`
- `TestNotifyObsStep::test_comment_non_blocking_nature`

### Integration Test (future)

- Spin up OTEL Collector locally, run notify-obs, verify trace received

## 8. Environment Configuration

### `.env.example` additions

```bash
# Observability — OTEL Collector endpoint for deployment events
# Suite mode: http://otel-collector:4318
OTEL_ENDPOINT=

# Optional auth headers for OTEL endpoint (e.g., "Authorization: Bearer <token>")
OTEL_HEADERS=
```

### Woodpecker Secrets Required

| Secret Name | Value Example | Notes |
|---|---|---|
| `otel_endpoint` | `http://otel-collector:4318` | OTEL Collector HTTP endpoint |
| `otel_headers` | `Authorization: Bearer <token>` | Optional, for authenticated collectors |

## 9. DORA Metrics Impact

| Metric | How notify-obs Enables |
|---|---|
| **Deployment Frequency** | Each successful `main` pipeline emits one deployment event |
| **Change Lead Time** | `git.commit.sha` + pipeline start time → deployment timestamp |
| **Change Failure Rate** | `deployment.status: success` vs failed pipeline events |
| **MTTR** | Correlated with rollback events (future work) |

## 10. References

- [OTLP HTTP Protocol](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/protocol/otlp.md)
- [DORA Deployment Events](https://dora.dev/capabilities/continuous-delivery/)
- [uFawkesObs Architecture](../../../uFawkesObs/docs/ARCHITECTURE.md)
