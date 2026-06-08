# DORA Metrics Log Format — Single Source of Truth

> All agents, skills, and shared library steps MUST use this format.
> Parseable by Obstackd OTEL Collector.

## Format Specification

All log lines use colon-delimited format with prefix `dora:`.

### Stage Events

```
dora:stage-start:<stageName>:<buildNumber>:<isoTimestamp>
dora:sha:<commitHash>
dora:stage-finish:<stageName>:<buildNumber>:<isoTimestamp>:<result>
```

| Field | Type | Example |
|---|---|---|
| `stageName` | string | `Build`, `Test`, `SAST`, `Push` |
| `buildNumber` | string | `42` |
| `isoTimestamp` | ISO 8601 | `2026-06-08T14:30:00Z` |
| `result` | enum | `success`, `failure`, `skipped` |

### DORA Metrics

```
dora:lead-time:<sha>:<seconds>
dora:deploy:<env>:<isoTimestamp>
dora:mttr:<sha>:<seconds>
dora:cfr:<sha>:<result>
```

| Metric | Field | Type | Example |
|---|---|---|---|
| Lead Time | `seconds` | int | `3600` |
| Deploy | `env` | string | `production`, `staging` |
| MTTR | `seconds` | int | `1800` |
| Change Failure Rate | `result` | enum | `pass`, `fail` |

### Error Events (on failure)

```
dora:stage-finish:<stageName>:<buildNumber>:<isoTimestamp>:failure
dora:error:<stageName>:<buildNumber>:<isoTimestamp>:<errorMessage>
```

## Groovy Utility

```groovy
// shared/vars/isoNow.groovy
def call() {
    return new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'", TimeZone.getTimeZone('UTC'))
}
```

## Log Line Examples

```
dora:stage-start:Build:42:2026-06-08T14:30:00Z
dora:sha:a1b2c3d
dora:stage-finish:Build:42:2026-06-08T14:31:15Z:success
dora:stage-start:Test:42:2026-06-08T14:31:16Z
dora:stage-finish:Test:42:2026-06-08T14:33:42Z:success
dora:lead-time:a1b2c3d:3600
dora:deploy:production:2026-06-08T14:35:00Z
dora:cfr:a1b2c3d:pass
```

## Anti-Patterns

- ❌ Using space-delimited format (use colon-delimited)
- ❌ Omitting the `dora:` prefix
- ❌ Omitting `buildNumber` from stage events
- ❌ Using freeform strings for `result` (use `success`/`failure`/`skipped`)
- ❌ Including PII or secrets in log lines
