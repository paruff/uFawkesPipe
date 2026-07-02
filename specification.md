# WP-009 — Full .woodpecker.yml Replacement and Test Suite Consolidation

**Type:** feat / refactor
**Depends on:** WP-001 (init), WP-004 (vuln-scan-fs), WP-005 (upload-defectdojo), WP-006 (notify-obs), WP-007 (QUICKSTART v0.2), WP-008 (README + pipeline-contract)
**Branch:** `feature/wp-009-woodpecker-replacement`

---

## 1. Problem

The current `.woodpecker.yml` is a monolithic 177-line pipeline with all steps inline. This creates several issues:

- **Maintainability:** All steps defined inline — no reuse, no parameterization
- **No stage separation:** Security, test, build, deploy stages are mixed
- **No parallelism:** All steps run sequentially even when independent
- **Hardcoded secrets handling:** Secrets referenced inline per step instead of centralized
- **No matrix support:** Cannot run tests across multiple language versions or configurations
- **Test suite fragmentation:** Tests scattered across `tests/unit/` with no clear integration/smoke/acceptance separation
- **DORA logging inconsistent:** Each step hand-rolls JSON logging instead of shared utility

The v0.2 platform needs a pipeline that:
- Uses Woodpecker's native pipeline features (matrix, dependencies, reusable steps)
- Separates stages clearly: validate → test → security → build → deploy
- Supports parallel execution where possible
- Centralizes configuration and secrets
- Enables test suite consolidation with clear separation of concerns

---

## 2. Requirements

### Functional

| # | Requirement | Rationale |
|---|---|---|
| F1 | Restructure `.woodpecker.yml` using Woodpecker v1.0+ pipeline features (stages, matrix, reusable steps) | Maintainability, parallelism |
| F2 | Define explicit pipeline stages: validate, test, security, build, publish, deploy | Clear separation of concerns |
| F3 | Extract common step logic into reusable YAML anchors or separate step files | DRY, consistency |
| F4 | Centralize secrets and environment variable management | Security, operational clarity |
| F5 | Enable matrix builds for multi-language test coverage | Polyglot support |
| F6 | Consolidate test suite into `tests/unit/`, `tests/integration/`, `tests/smoke/`, `tests/acceptance/` with clear ownership | Test strategy clarity |
| F7 | Create shared DORA logging utility for consistent structured logging | Observability standardization |
| F8 | Update `validate-pipeline-contract` step to use consolidated test structure | Single test entry point for pipeline validation |

### Non-Functional

| # | Requirement | Rationale |
|---|---|---|
| NF1 | Total pipeline duration should not increase (target: ≤ current) | Performance |
| NF2 | All existing security gates (Gitleaks, Trivy, SonarQube) preserved | Security compliance |
| NF3 | All existing tests pass without modification (only structural moves) | Regression prevention |
| NF4 | Woodpecker CLI `lint` passes on new pipeline YAML | Pipeline validity |

---

## 3. Acceptance Criteria

1. **Pipeline Structure**
   - `.woodpecker.yml` uses `stages:` with named stages: `validate`, `test`, `security`, `build`, `publish`, `deploy`
   - Steps within stages run in parallel where dependencies allow
   - Reusable step definitions via YAML anchors (`&step-name`) or separate files in `.woodpecker/steps/`

2. **Secrets & Environment**
   - All `from_secret:` references moved to top-level `environment:` or stage-level `environment:`
   - No inline secret references in step commands

3. **Test Consolidation**
   - `tests/unit/` — existing unit tests (93 tests), no changes to test logic
   - `tests/integration/` — new directory for cross-component tests (e.g., pipeline contract validation)
   - `tests/smoke/` — new directory for deployment smoke tests
   - `tests/acceptance/` — new directory for full E2E acceptance tests
   - `tests/conftest.py` — shared fixtures for all test types
   - `pytest.ini` updated with markers: `unit`, `integration`, `smoke`, `acceptance`

4. **DORA Logging Utility**
   - `scripts/dora-log.sh` or Python utility provides `dora_start`, `dora_end`, `dora_info`, `dora_warn`, `dora_error` functions
   - All pipeline steps use the shared utility instead of inline JSON

5. **Validation**
   - `woodpecker-cli pipeline lint .woodpecker.yml` passes
   - `pytest tests/unit/ -v` — 93 tests pass
   - `pytest tests/integration/ -v` — passes (new tests)
   - `pre-commit run --all-files` — all hooks pass

---

## 4. Dependencies

- **WP-001** — Artifact directories must exist for security scans
- **WP-004** — vuln-scan-fs step must be preserved in security stage
- **WP-005** — upload-defectdojo step must be preserved in security stage
- **WP-006** — notify-obs step must be preserved in deploy stage
- **WP-007** — QUICKSTART.md references updated pipeline commands
- **WP-008** — README.md and docs/pipeline-contract.md reference new structure

---

## 5. Out of Scope

- Adding new security tools (only restructuring existing)
- Changing test logic (only moving/organizing)
- Woodpecker server configuration changes
- Kubernetes deployment manifests (future work)
