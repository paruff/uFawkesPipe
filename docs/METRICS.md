# DORA Metrics Collection

Reading time: 8–12 minutes

## Purpose

This document describes how uFawkesPipe collects, emits, and reports the four DORA metrics:

1. **Lead Time for Changes** — Time from commit to production deploy
2. **Deployment Frequency** — Deploy events per unit time
3. **Mean Time to Restore** — Time from failure to recovery
4. **Change Failure Rate** — Failed deploys / total deploys

## Prerequisites

- uFawkesPipe running in suite mode (connected to uFawkesObs)
- OTEL Collector endpoint configured in `compose.yaml`
- uFawkesObs Loki/Prometheus/Grafana stack operational

## Metric Collection

### Pipeline-Level Events

Every pipeline stage emits structured JSON logs per `.agents/specs/dora-log-format.md`:

```json
{
  "@timestamp": "2026-06-30T14:30:00Z",
  "level": "info",
  "logger": "pipeline",
  "event": "stage-start",
  "stage": "Build",
  "pipeline": "123",
  "commit": "abc123"
}
```

### Stage Events

| Event | Description | Required Fields |
|-------|-------------|-----------------|
| `stage-start` | Stage begins | `stage`, `pipeline`, `commit` |
| `stage-finish` | Stage ends | `stage`, `pipeline`, `commit`, `result` |
| `stage-error` | Stage fails | `stage`, `pipeline`, `commit`, `error` |

### Deployment Events

Emitted by `notify-obs` step in `.woodpecker.yml`:

```json
{
  "@timestamp": "2026-06-30T14:35:00Z",
  "level": "info",
  "logger": "pipeline",
  "event.type": "deploy",
  "pipeline.number": "123",
  "git.commit": "abc123",
  "git.repo": "myorg/myapp",
  "git.branch": "main",
  "pipeline.duration_ms": "300000",
  "pipeline.status": "success"
}
```

## Metric Calculations

### Lead Time for Changes

```
lead_time = deploy_timestamp - commit_timestamp
```

- `commit_timestamp`: From `CI_COMMIT_TIMESTAMP` or git log
- `deploy_timestamp`: From deployment event

### Deployment Frequency

```
deployments_per_day = count(deploy_events) / days_in_window
```

### Mean Time to Restore

```
mttr = mean(restore_timestamp - failure_timestamp)
```

- `failure_timestamp`: From `stage-error` event with `result=failure`
- `restore_timestamp`: From subsequent successful `deploy` event

### Change Failure Rate

```
cfr = failed_deploys / total_deploys
```

- `failed_deploys`: Deployment events with `status=failure`
- `total_deploys`: All deployment events

## Queries (PromQL)

### Lead Time (p95)

```promql
histogram_quantile(0.95,
  sum by (le) (rate(dora_lead_time_seconds_bucket[5m]))
)
```

### Deployment Frequency (per day)

```promql
sum(rate(dora_deployments_total[1d]))
```

### MTTR

```promql
avg(dora_mttr_seconds)
```

### Change Failure Rate

```promql
sum(rate(dora_deployments_failed_total[5m])) /
sum(rate(dora_deployments_total[5m]))
```

## Woodpecker Native Prometheus Metrics (P3-3)

Distinct from the DORA log pipeline above: Woodpecker's server exposes its
own operational metrics directly, no OTEL Collector involved. Verified live
against `woodpeckerci/woodpecker-server:v3.15.0` during implementation
(this repo's standalone `compose.yaml` doesn't enable it — only
`compose.suite.yaml` sets `WOODPECKER_PROMETHEUS_AUTH_TOKEN`):

- `/metrics` returns **401** with no `Authorization` header, **403** with a
  wrong bearer token, **200** with `Authorization: Bearer $WOODPECKER_PROMETHEUS_AUTH_TOKEN`.
- Confirmed real metrics exposed: `woodpecker_pipeline_total_count`,
  `woodpecker_pending_steps`, `woodpecker_running_steps`,
  `woodpecker_waiting_steps`, `woodpecker_repo_count`,
  `woodpecker_worker_count`, `woodpecker_user_count`, plus the standard Go
  runtime metrics (`go_gc_*`, etc.).
- **Not exposed here:** per-pipeline duration or a success/failure
  breakdown — there is no `woodpecker_pipeline_duration_seconds` or
  equivalent. "Pipeline duration" and "success rate" (M2.2's acceptance
  criteria) have to come from the DORA log pipeline documented above
  (`pipeline.duration_ms`, `pipeline.status` in the `deploy` event), not
  from this endpoint. Treat this endpoint as fleet/queue health
  (repo/worker/user counts, queue depth), not a duration source.

**Scrape config** (add to Prometheus's own `scrape_configs`, run from
uFawkesObs or wherever Prometheus lives in suite mode):

```yaml
scrape_configs:
  - job_name: woodpecker
    scheme: http
    metrics_path: /metrics
    authorization:
      type: Bearer
      credentials: ${WOODPECKER_METRICS_TOKEN}
    static_configs:
      - targets: ["woodpecker-server:8000"]
```

`WOODPECKER_METRICS_TOKEN` is already declared in `.env.example` and wired
into `compose.suite.yaml`'s `woodpecker-server` service as
`WOODPECKER_PROMETHEUS_AUTH_TOKEN` — the same value goes on both sides.

## Pipeline Step Traces (P3-4)

Woodpecker CE has no native per-step OTEL span emission, so
`scripts/otel-trace.sh` is a wrapper: `source` it, call
`otel_span_start "<name>"`, then `otel_span_end "<name>" ["ok"|"error"]`. It
POSTs a minimal OTLP/HTTP JSON span per call to
`${OTEL_EXPORTER_OTLP_ENDPOINT}` with `:4317` rewritten to `:4318` (OTLP/HTTP
port — this wrapper has no gRPC/protobuf client). Every step in one
pipeline run shares one deterministic `trace_id` (derived from
`CI_REPO_NAME`/`CI_PIPELINE_NUMBER`), so Tempo renders them as sibling
spans under one trace.

Verified end-to-end during implementation against a real
`otel/opentelemetry-collector` container with a `debug` exporter: two spans
from the same simulated pipeline run showed up sharing one trace ID, with
distinct span IDs, correct names, correct elapsed time, and correct
`Ok`/`Error` status codes.

**Wired into:** `sast` (`sonarsource/sonar-scanner-cli`), `dast`
(`zaproxy/zap-stable`), `defectdojo-upload` (`curlimages/curl`) — the three
generator steps whose image actually has curl. **Not wired into:** `lint`,
`test`, `build`, `dependency-scan`, `image-scan`, `push`, `deploy` —
`docker:24-cli`, `aquasec/trivy`, `ghcr.io/google/osv-scanner` and
`python:3.12-slim` have neither curl nor a POST-capable `wget`, confirmed
while implementing this. The wrapper already no-ops safely if curl is
missing or `OTEL_EXPORTER_OTLP_ENDPOINT` is unset, so extending coverage
later (e.g. installing curl in a custom step image) needs no wrapper
changes.

## Grafana Dashboard

`grafana/dashboards/dora-metrics.json` is referenced here but **does not
exist in this repo** — confirmed absent while implementing P3-3. Building
the actual dashboard is uFawkesObs's side of M2.2/M2.6 (per
`MILESTONES.md`'s H2 repo boundary); this repo only needs to expose scrapeable
metrics correctly, which is now verified above.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No metrics in Grafana | Check OTEL Collector logs: `docker logs otel-collector` |
| Metrics show zero | Verify pipeline emits `stage-start`/`stage-finish` events |
| MTTR incorrect | Ensure deployment events include `pipeline.status` |

## Related

- `.agents/specs/dora-log-format.md` — Canonical log format
- `docs/ARCHITECTURE.md` — Cross-plane telemetry flow
- `docs/CHANGE_IMPACT_MAP.md` — Impact of pipeline changes on metrics
