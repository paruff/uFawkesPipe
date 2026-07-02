# uFawkesPipe — Specification v0.3

*CI/CD Plane of the Fawkes IDP Family*

**Status:** Draft — 2026-07-02
**Author:** Platform Engineering (solo contributor)
**Repo:** https://github.com/paruff/uFawkesPipe
**Supersedes:** v0.2 (2026-06-23)

---

## 1. Purpose and Scope

uFawkesPipe is the integration and delivery plane of the Fawkes IDP family. It provides a
**standardised pipeline contract** that polyglot application teams declare once (`.fawkespipe.yml`)
and the platform executes consistently across every push.

This specification covers the scope increase from the v0.2 baseline (Woodpecker + SonarQube +
Portainer + CNB + security scanning) to the v0.3 target state that adds:

- An **automated acceptance test suite** (`tests/acceptance/`) that verifies the full golden path:
  stack health, authentication, pipeline execution, security scanning, and deployment
- A **Portainer health and authentication verification** layer — currently untested
- A **golden-path pipeline simulation** that validates the end-to-end flow from build trigger
  to SonarQube analysis to Portainer deploy webhook
- **Service-level authentication tests** for Woodpecker, SonarQube, and Portainer

**Out of scope for v0.3:**
- DefectDojo provisioning and integration (Q1 remains open from v0.2)
- Actual container image building (simulated pipeline triggers only)
- Kubernetes promotion path testing
- External GitHub webhook integration (Woodpecker token scoping)
- Performance/stress testing

---

## 2. Personas and JTBD

| Persona | Job To Be Done |
| --- | --- |
| **App developer** | Push code and get a pass/fail signal with actionable security findings in under 10 min |
| **Platform engineer** | Onboard a new repo to the pipeline in < 30 min with zero per-app pipeline YAML |
| **Platform engineer** (v0.3 new) | Start the stack with `make up` and run one command to verify the entire golden path works |
| **Security engineer** | See all secret and CVE findings aggregated in DefectDojo without touching CI config |
| **DORA practitioner** | Consume deployment frequency and lead-time events from uFawkesObs without manual tagging |

---

## 3. Functional Requirements — v0.3 Acceptance Test Suite

### 3.1 Stack Health Verification

- FR-3.1.1: Every service in `compose.yaml` (Woodpecker server, Woodpecker agent, SonarQube,
  Portainer) must respond to a health check or API endpoint within 30 seconds of `make up`.
- FR-3.1.2: Woodpecker UI must be accessible at `http://localhost:8000` with HTTP 200.
- FR-3.1.3: Woodpecker `/healthz` endpoint must return HTTP 200.
- FR-3.1.4: SonarQube `/api/system/status` must return `{"status": "UP"}` with HTTP 200.
- FR-3.1.5: SonarQube UI must be accessible at `http://localhost:9001` with HTTP 200 or 302.
- FR-3.1.6: Portainer UI must be accessible at `https://localhost:9443`.
- FR-3.1.7: Portainer API must be accessible; first-run admin initialization must succeed
  via `POST /api/users/admin/init` with a generated password.

### 3.2 Authentication Verification

- FR-3.2.1: Woodpecker must be open-access (`WOODPECKER_OPEN=true`) — no authentication
  required when accessing the UI and API. The test must verify this is the configured state.
- FR-3.2.2: SonarQube must authenticate with default credentials (`admin`/`admin`) and
  return a valid session token. The test must also verify the default password can be
  changed (but not leave the changed password in place).
- FR-3.2.3: Portainer must complete first-run admin initialization and return a valid
  JWT authentication token from `POST /api/auth`. The test must use the token to access
  an authenticated endpoint (`GET /api/endpoints`).

### 3.3 Golden Path Pipeline Simulation

- FR-3.3.1: A Woodpecker pipeline for uFawkesPipe itself must exist and be triggerable
  (verified by inspecting Woodpecker API or UI for the repo).
- FR-3.3.2: The pipeline must contain all expected stages: validate, test, security, build,
  publish, deploy — in correct dependency order.
- FR-3.3.3: The Gitleaks secrets-scan step must be present as a hard gate.
- FR-3.3.4: The Trivy vulnerability scan steps must be present (filesystem scan on all
  branches, image scan on main only).

### 3.4 Security Verification

- FR-3.4.1: SonarQube must accept a project creation via API, simulating the SAST stage.
- FR-3.4.2: The Woodpecker pipeline must produce security artifacts in the expected
  directory structure (`artifacts/security/gitleaks.json`, `artifacts/security/trivy-repo.json`).

### 3.5 Deployment & Observability

- FR-3.5.1: Portainer must expose a webhook-capable stack endpoint. The test verifies
  Portainer is configured for CD, not that a specific webhook fires.
- FR-3.5.2: The `notify-obs` step must be present in the pipeline and emit a DORA-structured
  deployment event payload.

### 3.6 Test Infrastructure

- FR-3.6.1: Tests must use `@pytest.mark.acceptance` marker for targeting.
- FR-3.6.2: Tests must gracefully skip (`pytest.skip`) when the compose stack is not running.
- FR-3.6.3: Tests must be runnable via `make test-acceptance`.
- FR-3.6.4: Tests must not modify production state — SonarQube password changes must be
  reverted; Portainer admin initialization must use a test-only password.
- FR-3.6.5: All tests must produce binary pass/fail results — no "warning" or "partial" outcomes.

### 3.7 Documentation

- FR-3.7.1: README.md must document the acceptance test suite, its purpose, and how to run it.
- FR-3.7.2: `docs/KNOWN_LIMITATIONS.md` must be updated to reflect that acceptance tests now exist.

---

## 4. Non-Functional Requirements

| Concern | Requirement |
| --- | --- |
| **Execution time** | Full acceptance suite < 5 minutes from `make test-acceptance` (excluding service startup) |
| **Idempotency** | Tests must be re-runnable without side effects; no state left behind |
| **Skip-safe** | All tests skip gracefully when stack is not running — no false failures |
| **Test isolation** | Tests must not depend on prior test state; each test file independently runnable |
| **Error messages** | All assertions must produce clear error messages identifying what failed |
| **Compose lifecycle** | Tests must not call `make up` or `make down`; they only verify a running stack |

---

## 5. Acceptance Criteria

See `docs/acceptance-criteria.md` for the full binary pass/fail criteria map.
Summary acceptance criteria:

1. `make test-acceptance` passes with zero failures when the stack is running and
   all services are healthy.
2. `make test-acceptance` produces 0 failures (only skips) when the stack is not
   running — no false positives.
3. All 8 service health checks pass (Woodpecker UI, Woodpecker healthz, Woodpecker agent,
   SonarQube status, SonarQube UI, Portainer UI, Portainer API init, Portainer auth).
4. SonarQube authentication succeeds with default credentials.
5. Portainer first-run admin initialization succeeds and returns a valid JWT.
6. Woodpecker pipeline for uFawkesPipe repo exists and contains all expected stages
   in correct dependency order.
7. Gitleaks secrets-scan step is present as a hard gate.
8. Trivy vulnerability scan steps are present with correct branch constraints.

---

## 6. Open Questions (block implementation if unresolved)

| # | Question | Owner | Target |
| --- | --- | --- | --- |
| Q1 | Is DefectDojo deployed on `fawkes-net` before this work starts? | Platform engineer | Before DefectDojo tests |
| Q2 | Which OCI registry is canonical for v0.3? DockerHub or self-hosted Harbor? | Platform engineer | Before build simulation tests |
| Q3 | `notify-obs` payload schema — confirm field names with uFawkesObs team | Platform engineer | Before observability tests |

(Questions Q1-Q3 carried forward from v0.2 — no blockers for v0.3 scope.)
