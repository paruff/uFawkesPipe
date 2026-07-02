# Acceptance Criteria — uFawkesPipe v0.3

> Binary pass/fail criteria for the automated acceptance test suite.
> Each AC maps to a specific test function in `tests/acceptance/`.
> All tests use `@pytest.mark.acceptance` and skip gracefully when the stack is not running.

---

## AC-01: Stack Health — All Services Accessible

| Field | Value |
|-------|-------|
| **AC ID** | AC-01 |
| **Requirement** | FR-3.1.1 |
| **Given** | `make up` has completed and all compose services show "running" |
| **When** | `make test-acceptance` runs the health verification tests |
| **Then** | Woodpecker UI returns HTTP 200, Woodpecker `/healthz` returns HTTP 200, Woodpecker agent gRPC port is reachable, SonarQube `/api/system/status` returns `{"status":"UP"}`, SonarQube UI returns HTTP 200/302, Portainer UI serves HTTPS on :9443 |
| **Priority** | must-have |
| **Test method** | acceptance (`tests/acceptance/test_01_stack_health.py`) |
| **Measurable** | true — HTTP status codes, JSON body assertions |

---

## AC-02: Woodpecker Health Verification

| Field | Value |
|-------|-------|
| **AC ID** | AC-02 |
| **Requirement** | FR-3.1.2, FR-3.1.3 |
| **Given** | Woodpecker server is running on :8000 |
| **When** | HTTP GET to `http://localhost:8000` and `http://localhost:8000/healthz` |
| **Then** | Both return HTTP 200. `/healthz` response body contains success indicator. |
| **Priority** | must-have |
| **Test method** | acceptance |
| **Measurable** | true |

---

## AC-03: SonarQube Health Verification

| Field | Value |
|-------|-------|
| **AC ID** | AC-03 |
| **Requirement** | FR-3.1.4, FR-3.1.5 |
| **Given** | SonarQube is running on :9001 (mapped from :9000) |
| **When** | HTTP GET to `http://localhost:9000/api/system/status` and `http://localhost:9001` |
| **Then** | Status endpoint returns HTTP 200 with `{"status":"UP"}`. UI returns HTTP 200 or 302. |
| **Priority** | must-have |
| **Test method** | acceptance |
| **Measurable** | true |

---

## AC-04: Portainer Health Verification

| Field | Value |
|-------|-------|
| **AC ID** | AC-04 |
| **Requirement** | FR-3.1.6, FR-3.1.7 |
| **Given** | Portainer is running on :9443 (HTTPS) |
| **When** | HTTPS GET to `https://localhost:9443` (with TLS verification disabled for localhost) |
| **Then** | Returns HTTP 200 (UI accessible). First-run admin initialization via `POST /api/users/admin/init` succeeds with HTTP 200/201 and generates a valid admin user. |
| **Priority** | must-have |
| **Test method** | acceptance |
| **Measurable** | true |

---

## AC-05: Woodpecker Open Access Verification

| Field | Value |
|-------|-------|
| **AC ID** | AC-05 |
| **Requirement** | FR-3.2.1 |
| **Given** | Woodpecker is configured with `WOODPECKER_OPEN=true` in `compose.yaml` |
| **When** | HTTP GET to `http://localhost:8000/api/user` (no auth header) |
| **Then** | Returns user data without requiring authentication. (If `WOODPECKER_OPEN=false` in production, this test verifies the compose configuration intent.) |
| **Priority** | must-have |
| **Test method** | acceptance |
| **Measurable** | true |

---

## AC-06: SonarQube Authentication

| Field | Value |
|-------|-------|
| **AC ID** | AC-06 |
| **Requirement** | FR-3.2.2 |
| **Given** | SonarQube is running with default credentials (`admin`/`admin`) |
| **When** | HTTP POST to `http://localhost:9000/api/authentication/login` with `login=admin&password=admin` |
| **Then** | Returns HTTP 200 with a valid session cookie or token. The authenticated session can access `GET /api/projects/search`. |
| **Priority** | must-have |
| **Test method** | acceptance |
| **Measurable** | true |

---

## AC-07: Portainer First-Run Initialization + Authentication

| Field | Value |
|-------|-------|
| **AC ID** | AC-07 |
| **Requirement** | FR-3.2.3 |
| **Given** | Portainer is running on :9443, fresh or already initialized |
| **When** | (1) `POST /api/users/admin/init` with `Username=admin` and `Password=<generated>` for first-run, or (2) `POST /api/auth` with `{"Username":"admin","Password":"<known>"}` if already initialized |
| **Then** | Returns a valid JWT token (`jwt` field). Token can be used to access `GET /api/endpoints` with HTTP 200. |
| **Priority** | must-have |
| **Test method** | acceptance |
| **Measurable** | true |

---

## AC-08: Woodpecker Pipeline Structure Verification

| Field | Value |
|-------|-------|
| **AC ID** | AC-08 |
| **Requirement** | FR-3.3.1, FR-3.3.2 |
| **Given** | uFawkesPipe's `.woodpecker.yml` defines the CI pipeline |
| **When** | The test parses `.woodpecker.yml` and inspects step definitions |
| **Then** | All expected steps are present: `init`, `lint-yaml`, `lint-shell`, `validate-agents`, `unit-tests`, `integration-tests`, `contract-tests`, `secrets-scan`, `vuln-scan-fs`, `vuln-scan-image`, `build-image`, `upload-defectdojo`, `notify-obs`. Steps have correct `depends_on` ordering (init → lint → test → security → build → publish → deploy). |
| **Priority** | must-have |
| **Test method** | acceptance |
| **Measurable** | true |

---

## AC-09: Security Gates Verification

| Field | Value |
|-------|-------|
| **AC ID** | AC-09 |
| **Requirement** | FR-3.3.3, FR-3.3.4 |
| **Given** | `.woodpecker.yml` defines the security stage |
| **When** | The test inspects the `secrets-scan`, `vuln-scan-fs`, and `vuln-scan-image` step definitions |
| **Then** | `secrets-scan` uses `gitleaks detect` with `--exit-code=1` (hard gate). `vuln-scan-fs` runs on all branches (no `when` constraint or `when.event: [push, pull_request]`). `vuln-scan-image` runs on `branch: main` only. |
| **Priority** | must-have |
| **Test method** | acceptance |
| **Measurable** | true |

---

## AC-10: SonarQube Project Creation (SAST Simulation)

| Field | Value |
|-------|-------|
| **AC ID** | AC-10 |
| **Requirement** | FR-3.4.1 |
| **Given** | SonarQube is running and authenticated with admin credentials |
| **When** | `POST /api/projects/create` with `name=acceptance-test-project` and `project=acceptance_test_project` |
| **Then** | Returns HTTP 200. Subsequent `GET /api/projects/search?projects=acceptance_test_project` returns the created project. Project is deleted after test to leave no state. |
| **Priority** | should-have |
| **Test method** | acceptance |
| **Measurable** | true |

---

## AC-11: Portainer CD Readiness Verification

| Field | Value |
|-------|-------|
| **AC ID** | AC-11 |
| **Requirement** | FR-3.5.1 |
| **Given** | Portainer is initialized and authenticated |
| **When** | The test accesses `GET /api/endpoints` with a valid JWT |
| **Then** | Returns at least one endpoint (the local Docker environment). Portainer is configured as a CD target. |
| **Priority** | should-have |
| **Test method** | acceptance |
| **Measurable** | true |

---

## AC-12: Observability Event Step Verification

| Field | Value |
|-------|-------|
| **AC ID** | AC-12 |
| **Requirement** | FR-3.5.2 |
| **Given** | `.woodpecker.yml` defines the deploy stage |
| **When** | The test inspects the `notify-obs` step definition |
| **Then** | Step exists, uses `curlimages/curl:8.6.0`, depends on `upload-defectdojo`, and emits a structured JSON payload containing `service.name`, `deployment.environment`, `deployment.version`, `deployment.status`, and `git.commit.sha`. |
| **Priority** | should-have |
| **Test method** | acceptance |
| **Measurable** | true |

---

## AC-13: Acceptance Suite Skip-Safety

| Field | Value |
|-------|-------|
| **AC ID** | AC-13 |
| **Requirement** | FR-3.6.2 |
| **Given** | The compose stack is **not** running |
| **When** | `make test-acceptance` runs |
| **Then** | All tests skip (not fail). Result is 0 failures, N skips. |
| **Priority** | must-have |
| **Test method** | acceptance |
| **Measurable** | true — verify with `docker compose down` then `make test-acceptance` |

---

## AC-14: Acceptance Suite Idempotency

| Field | Value |
|-------|-------|
| **AC ID** | AC-14 |
| **Requirement** | FR-3.6.3, FR-3.6.4 |
| **Given** | The stack is running |
| **When** | `make test-acceptance` runs twice in succession |
| **Then** | Both runs produce identical results (same pass/fail/skip counts). No state changes persist between runs. |

---

## AC-15: Makefile Target Integration

| Field | Value |
|-------|-------|
| **AC ID** | AC-15 |
| **Requirement** | FR-3.6.3 |
| **Given** | The Makefile has a `test-acceptance` target |
| **When** | `make test-acceptance` is invoked |
| **Then** | Target runs `pytest tests/acceptance/ -v --tb=short` (or equivalent). Target is documented in `make help` output. |
| **Priority** | must-have |
| **Test method** | unit — verify Makefile target syntax |

---

## Test File → AC Mapping

| Test File | ACs Covered |
|-----------|-------------|
| `tests/acceptance/test_01_stack_health.py` | AC-01, AC-02, AC-03, AC-04 |
| `tests/acceptance/test_02_authentication.py` | AC-05, AC-06, AC-07 |
| `tests/acceptance/test_03_pipeline_structure.py` | AC-08, AC-09, AC-12 |
| `tests/acceptance/test_04_security_simulation.py` | AC-10 |
| `tests/acceptance/test_05_portainer_cd.py` | AC-11 |
| `tests/acceptance/test_06_suite_behavior.py` | AC-13, AC-14 |

---

## Governance Alignment

| Policy | Status |
|--------|--------|
| Pipeline stage requirements | ✅ AC-08, AC-09 verify all expected stages |
| Security gates | ✅ AC-09 verifies Gitleaks hard gate and Trivy scans |
| Image pinning | ✅ AC-12 verifies pinned curl image |
| Secret hygiene | ✅ No secrets in test code; auth tokens are test-only |
| DORA logging | ✅ AC-12 verifies structured event payload |
| Naming conventions | ✅ Test files follow `test_NN_description.py` pattern |
