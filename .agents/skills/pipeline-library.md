---
name: pipeline-library
description: Woodpecker CI pipeline conventions, DORA logging, step patterns, and idempotency rules for uFawkesPipe
applies: .woodpecker.yml, .github/workflows/**/*.yml, compose.yaml
---

# Pipeline Library — Woodpecker CI Standards

> Load this skill before creating or editing any `.woodpecker.yml` or `.github/workflows/` file.

## File Convention

- Main pipeline: `.woodpecker.yml` (Woodpecker native format)
- Reusable workflow templates: `.github/workflows/reusable-*.yml` (GitHub Actions for CI validation)
- Service definitions for local CI: `compose.yaml`

## Step Template

```yaml
# .woodpecker.yml step template
- name: my-step
  image: alpine:3.20
  commands:
    # 1. Validate required params (via env vars or shell)
    - |
      if [ -z "${REQUIRED_PARAM:-}" ]; then
        echo '{"@timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","level":"error","logger":"step","message":"REQUIRED_PARAM is required"}'
        exit 1
      fi

    # 2. Log start per .agents/specs/dora-log-format.md
    - echo '{"@timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","level":"info","logger":"pipeline","event":"stage-start","stage":"MyStep","pipeline":"${CI_PIPELINE_NUMBER}","commit":"${CI_COMMIT_SHA}"}'

    # 3. Idempotency check — skip if already done
    - |
      if [ -f ".my-step-completed" ]; then
        echo '{"@timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","level":"info","logger":"step","message":"already completed, skipping","step":"my-step"}'
        exit 0
      fi

    # 4. Core logic with error handling
    - some-command "${REQUIRED_PARAM}"
    - touch .my-step-completed
    - echo '{"@timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","level":"info","logger":"pipeline","event":"stage-finish","stage":"MyStep","pipeline":"${CI_PIPELINE_NUMBER}","commit":"${CI_COMMIT_SHA}","result":"success"}'

  # Failure handling via shell trap or explicit checks
  when:
    event: [push, pull_request]
```

## DORA Logging — Strict Rules

> Full spec in `.agents/specs/dora-log-format.md`. Use `date -u +%Y-%m-%dT%H:%M:%SZ` for timestamps.

| Rule         | Details                                    |
| ------------ | ------------------------------------------ |
| Format       | JSON structured logs                       |
| Required     | `event: stage-start \| stage-finish \| stage-error` |
| Fields       | `stage`, `pipeline`, `commit`, `result`    |
| Timestamps   | ISO 8601 UTC via `date -u +%Y-%m-%dT%H:%M:%SZ` |
| Build number | Include `CI_PIPELINE_NUMBER` in stage events |
| No PII       | Never log credentials, tokens, or secrets  |

## Idempotency Patterns

### Pattern 1: Marker File (preferred)

```yaml
- |
  if [ -f ".step-done" ]; then
    echo '{"...event":"stage-finish","result":"skipped"}'
    exit 0
  fi
- sh "..."
- touch .step-done
```

### Pattern 2: Check Output

```yaml
- |
  result=$(some-check-command)
  if [ "$result" = "already-done" ]; then
    exit 0
  fi
```

## Credential Handling

```yaml
# ✅ CORRECT — secrets from Woodpecker secret store
- name: push-image
  image: plugins/docker:24
  settings:
    registry: docker.io
    username:
      from_secret: dockerhub_username
    password:
      from_secret: dockerhub_password

# ❌ WRONG — password visible in process table
- sh "docker login -u myuser -p mypassword"

# ❌ WRONG — password visible in shell expansion
- sh "docker login -u ${DOCKER_USER} -p ${DOCKER_PASS}"
```

## Error Handling

```yaml
commands:
  - your-command || rc=$?
  - |
    if [ $rc -ne 0 ]; then
      # ALWAYS capture artifacts before exiting
      mkdir -p artifacts
      cp -r reports/* artifacts/ 2>/dev/null || true
      echo '{"@timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","level":"error","logger":"pipeline","event":"stage-error","stage":"YourStep","pipeline":"${CI_PIPELINE_NUMBER}","commit":"${CI_COMMIT_SHA}","error":"command failed"}'
      exit $rc
    fi
```
