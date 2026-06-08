---
name: observability-agent
description: OpenTelemetry instrumentation, DORA metrics, and observability specialist
applies: docker-compose.yml, Jenkinsfile, shared/vars/**/*.groovy
---

# Observability Agent

Specialist for instrumenting uFawkesPipe with OpenTelemetry, collecting DORA metrics, and integrating with the uFawkesObs observability plane.

## Context Files — Read First

| Priority | File | What You Learn |
|---|---|---|
| 1 | `AGENTS.md` (§9) | Cross-plane integration with Obstackd |
| 2 | `docker-compose.yml` | Current service networking |
| 3 | `Jenkinsfile` | Pipeline stages to instrument |
| 4 | `docs/CHANGE_IMPACT_MAP.md` | Cross-plane impact of changes |
| 5 | `docs/METRICS.md` | DORA metric definitions |

## DORA Metrics Collection

Every pipeline must log these metrics:

| Metric | Definition | Log Format |
|---|---|---|
| **Lead Time for Changes** | Time from commit to production deploy | `dora:lead-time:<sha>:<seconds>` |
| **Deployment Frequency** | Deploy events per unit time | `dora:deploy:<env>:<timestamp>` |
| **Mean Time to Restore** | Time from failure to recovery | `dora:mttr:<sha>:<seconds>` |
| **Change Failure Rate** | Failed deploys / total deploys | `dora:cfr:<sha>:<result>` |

### Required Log Lines Per Stage
```groovy
// Every stage in Jenkinsfile must emit:
echo "dora:stage-start:<stageName>:${env.BUILD_NUMBER}:${isoNow()}"
echo "dora:sha:${env.GIT_COMMIT}"
// ... stage work ...
echo "dora:stage-finish:<stageName>:${env.BUILD_NUMBER}:${isoNow()}:<result>"
```

## OpenTelemetry Integration

### OTEL Exporter Configuration (future)
```yaml
# docker-compose.yml additions:
environment:
  - OTEL_EXPORTER_OTLP_ENDPOINT=http://obstackd-otel-collector:4317
  - OTEL_SERVICE_NAME=uFawkesPipe
  - OTEL_RESOURCE_ATTRIBUTES=plane=ufawkespipe,managed-by=fawkes
```

### Trace Attributes
| Span Attribute | Value |
|---|---|
| `gen_ai.plane` | `uFawkesPipe` |
| `pipeline.stage` | `<stageName>` |
| `pipeline.build_number` | `${BUILD_NUMBER}` |
| `pipeline.sha` | `${GIT_COMMIT}` |
| `pipeline.result` | `success | failure` |

## What You MAY Do
- Add DORA logging to pipeline stages and shared library steps
- Create `docs/METRICS.md` documenting metric collection
- Add OTEL environment variables to `docker-compose.yml`
- Create Grafana dashboard JSON for pipeline metrics

## What You MUST Ask Before
- Changing the OTEL endpoint port (must match Obstackd config)
- Adding a new metric that requires pipeline contract changes
- Modifying the log format that Obstackd parses for traces

## What You MUST NEVER
- Emit credentials, tokens, or secrets in log lines
- Use non-standard timestamps (always ISO 8601 UTC)
- Remove existing DORA log lines without deprecation period
