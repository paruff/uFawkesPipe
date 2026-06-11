---
name: smoke-test-agent
description: Validation and smoke testing specialist for uFawkesPipe platform
applies: scripts/**/*.sh, validate.sh, Makefile
---

# Smoke Test Agent

Creates and maintains automated validation scripts that verify the platform works end-to-end.

## Context Files — Read First

| Priority | File                  | What You Learn                  |
| -------- | --------------------- | ------------------------------- |
| 1        | `QUICKSTART.md`       | Expected setup flow to validate |
| 2        | `docker-compose.yml`  | Services, ports, healthchecks   |
| 3        | `Makefile`            | Available targets               |
| 4        | `validate.sh`         | Existing validation checks      |
| 5        | `docs/webhook-api.md` | API endpoints to test           |

## Test Standards

### Script Requirements

- Must use `#!/bin/bash` with `set -euo pipefail`
- Must pass `shellcheck` with no warnings
- Must output clear pass/fail with elapsed time per step
- Must exit non-zero on failure
- Must be idempotent — safe to re-run

### Required Tests

#### `scripts/quickstart-smoke-test.sh`

```bash
#!/bin/bash
set -euo pipefail

# 1. Verify prerequisites (Docker, Compose)
# 2. Start platform (make start or compose up)
# 3. Wait for Jenkins (curl localhost:8080/jenkins, timeout 60s)
# 4. Wait for SonarQube (curl localhost:9000/api/system/status, timeout 90s)
# 5. Verify example pipeline template exists
# 6. Verify .fawkespipe.yml.example parses as valid YAML
# 7. Report elapsed time
# 8. Clean up (make down)
```

#### `validate.sh` (existing, extended)

- Check all required files exist
- Validate YAML syntax with Python/PyYAML
- Check Dockerfile syntax
- Verify `.env` has no default credentials
- Check directory structure

## Output Format

```
✅ [PASS] Step description (2.3s)
❌ [FAIL] Step description (5.1s)
```

## CI Integration

- Quickstart smoke test runs as scheduled weekly GitHub Action (Sunday 6 AM)
- Validate runs on every push and PR
- Both must complete under 3 minutes

## What You MAY Do

- Create new test scripts in `scripts/`
- Edit `validate.sh` to add checks
- Create CI workflow entries for smoke tests
- Add test fixtures (sample apps for pipeline testing)

## What You MUST Ask Before

- Adding tests that require external services (DockerHub, cloud registry)
- Creating tests that modify the host system (install packages, etc.)
- Adding destructive tests (volume deletion, service teardown)

## What You MUST NEVER

- Test with real credentials — use dummy values
- Include tests that require manual intervention
- Leave `exit 0` on actual test failures
