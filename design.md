# WP-009 — Design: Full .woodpecker.yml Replacement and Test Suite Consolidation

## 1. Impacted Components

| Component | File | Change |
|---|---|---|
| Main Pipeline | `.woodpecker.yml` | Complete restructure with stages, matrix, reusable steps |
| Test Structure | `tests/` | Consolidate into unit/integration/smoke/acceptance |
| Shared Fixtures | `tests/conftest.py` | Expand for all test types |
| DORA Logging | `scripts/dora-log.sh` | New shared utility |
| Pipeline Steps | `.woodpecker/steps/` | New directory for reusable step definitions |

---

## 2. Pipeline Architecture Redesign

### 2.1 Stage Definition

```yaml
stages:
  - validate      # Lint, syntax checks (fast, parallel)
  - test          # Unit + integration tests (parallel matrix)
  - security      # Secret scan, vuln scan, SAST (sequential gates)
  - build         # Container image build (CNB/Docker)
  - publish       # Push to registry, upload security artifacts
  - deploy        # Suite mode: notify-obs, integration deploy
```

### 2.2 Stage Dependencies

```
validate
  ├── lint-yaml (parallel)
  ├── lint-shell (parallel)
  └── lint-markdown (parallel)  ← NEW

test (depends on: validate)
  ├── unit-tests (matrix: python 3.11, 3.12)
  ├── integration-tests (parallel)
  └── contract-tests (parallel)

security (depends on: test)
  ├── secrets-scan (hard gate)
  ├── sast-sonarqube
  ├── vuln-scan-fs
  └── vuln-scan-image (main only)

build (depends on: security)
  ├── build-image (CNB/Docker matrix)

publish (depends on: build)
  ├── push-image (main only)
  ├── upload-defectdojo (main only)

deploy (depends on: publish)
  ├── notify-obs (main only)
  └── integration-deploy (suite mode only)
```

---

## 3. Reusable Step Definitions

Create `.woodpecker/steps/` with YAML anchors for common patterns:

```yaml
# .woodpecker/steps/common.yaml
x-dora-logging: &dora-logging
  commands:
    - source /drone/src/scripts/dora-log.sh
    - dora_start "${CI_STEP_NAME}"

x-gitleaks-scan: &gitleaks-scan
  image: zricethezav/gitleaks:v8.18.2
  <<: *dora-logging
  commands:
    - gitleaks detect --source=. --report-format=json --report-path=artifacts/security/gitleaks.json --exit-code=1

x-trivy-fs: &trivy-fs
  image: aquasec/trivy:latest
  <<: *dora-logging
  commands:
    - trivy fs --format json --output artifacts/security/trivy-repo.json --no-progress .

# ... etc
```

---

## 4. Test Suite Consolidation

### 4.1 Directory Structure

```
tests/
├── conftest.py              # Shared fixtures + pytest markers
├── pytest.ini               # Markers: unit, integration, smoke, acceptance
├── requirements.txt         # Test dependencies
├── unit/                    # Pure unit tests (fast, isolated)
│   ├── test_artifact_dirs.py
│   ├── test_compose_network.py
│   ├── test_docker_compose_validation.py
│   └── test_woodpecker_yml.py
├── integration/             # Cross-component tests
│   ├── test_pipeline_contract.py
│   └── test_compose_integration.py
├── smoke/                   # Deployment smoke tests
│   ├── test_woodpecker_health.py
│   └── test_sonarqube_health.py
└── acceptance/              # Full E2E tests
    └── test_full_pipeline.py
```

### 4.2 Pytest Markers

```ini
# pytest.ini
[pytest]
markers =
    unit: Unit tests (fast, no external deps)
    integration: Integration tests (require Docker/services)
    smoke: Smoke tests (require running stack)
    acceptance: Acceptance tests (full E2E)
```

---

## 5. DORA Logging Utility

### 5.1 `scripts/dora-log.sh`

```bash
#!/usr/bin/env bash
# Shared DORA structured logging for Woodpecker pipeline steps

dora_emit() {
  local level="$1"
  local logger="$2"
  local message="$3"
  local extra_fields="${4:-}"

  cat <<EOF | jq -c .
{
  "@timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "level": "$level",
  "logger": "$logger",
  "message": "$message",
  "pipeline": "${CI_PIPELINE_NUMBER:-unknown}",
  "repo": "${CI_REPO:-unknown}",
  "step": "${CI_STEP_NAME:-unknown}"
  ${extra_fields}
}
EOF
}

dora_start() { dora_emit "info" "$1" "Starting $1"; }
dora_end()   { dora_emit "info" "$1" "Completed $1"; }
dora_info()  { dora_emit "info" "$1" "$2"; }
dora_warn()  { dora_emit "warn" "$1" "$2"; }
dora_error() { dora_emit "error" "$1" "$2"; }
```

### 5.2 Usage in Steps

```yaml
- name: secrets-scan
  image: zricethezav/gitleaks:v8.18.2
  commands:
    - source /drone/src/scripts/dora-log.sh
    - dora_start "secrets-scan"
    - gitleaks detect ...
    - dora_end "secrets-scan"
```

---

## 6. File Mapping

| Source | Action |
|---|---|
| `.woodpecker.yml` (177 lines) | Complete rewrite → staged pipeline |
| `tests/unit/*.py` (4 files) | No logic changes, only location |
| `tests/conftest.py` | Expand fixtures for all test types |
| `tests/requirements.txt` | Add integration/smoke/acceptance deps |
| `pytest.ini` | Add markers, configure test paths |
| `scripts/dora-log.sh` | **New file** |
| `.woodpecker/steps/common.yaml` | **New file** |

---

## 7. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Pipeline fails due to stage dependency ordering | Medium | Test locally with `woodpecker-cli pipeline lint` and dry-run |
| Test consolidation breaks imports | Low | Move files without changing code; update `__init__.py` only |
| DORA logging utility not available in container | Medium | COPY script into builder image or use inline source |
| Woodpecker version incompatibility | Low | Use stable Woodpecker v1 features only |
| Increased pipeline duration | Low | Enable parallelism in validate/test stages; measure and tune |
