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
- OTEL Collector endpoint configured in `docker-compose.yml`
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

## Grafana Dashboard

See `grafana/dashboards/dora-metrics.json` for a pre-built dashboard.

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
