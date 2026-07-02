# Design — uFawkesPipe Acceptance Test Suite v0.3

> Technical architecture for the automated acceptance test suite.
> Consumes: specification.md, acceptance-criteria.md
> Produces: tasks.json (via plan agent)

---

## 1. Architecture Overview

The acceptance test suite is a **pytest-based test harness** that verifies the uFawkesPipe
stack against the golden path. It lives in `tests/acceptance/` alongside existing smoke and
integration tests.

**Design philosophy:**
- **Compose-aware, not compose-controlling** — Tests verify a running stack; they do not start
  or stop it. Skip gracefully when the stack is down.
- **HTTP-native** — All service interactions use direct HTTP(S) calls. No Selenium, no browser
  automation. This is an API-and-configuration verification, not a UI test.
- **Binary pass/fail** — Every assertion either passes or fails. No "warning" or "partial"
  outcomes. This is acceptance testing, not linting.
- **No side effects** — Tests initialize what they need (Portainer admin, SonarQube project)
  and clean up after themselves. Two consecutive runs produce identical results.
- **Pipless** — Tests do not trigger actual Woodpecker pipelines. Pipeline structure is
  verified by parsing `.woodpecker.yml` directly. This avoids needing GitHub webhooks,
  OAuth tokens, and a full CI run for every test.

---

## 2. Component Map

```
tests/acceptance/
├── __init__.py                  # Package marker
├── conftest.py                  # Shared fixtures (compose check, auth tokens, HTTP helpers)
├── test_01_stack_health.py      # AC-01, AC-02, AC-03, AC-04 — all service health checks
├── test_02_authentication.py    # AC-05, AC-06, AC-07 — Woodpecker, SonarQube, Portainer auth
├── test_03_pipeline_structure.py # AC-08, AC-09, AC-12 — .woodpecker.yml step inspection
├── test_04_security_simulation.py # AC-10 — SonarQube project create/delete
├── test_05_portainer_cd.py      # AC-11 — Portainer endpoint verification
└── test_06_suite_behavior.py    # AC-13, AC-14 — skip-safety, idempotency
```

### Dependency Order

Tests are numbered but **not sequenced** — pytest runs them independently. The numbering
reflects logical grouping:

```
test_01 (health) ──► no dependencies, pure HTTP reachability
test_02 (auth)   ──► depends on services being healthy (implied by AC-01)
test_03 (pipeline structure) ──► reads .woodpecker.yml from disk, no services needed
test_04 (security simulation) ──► needs SonarQube auth (AC-06)
test_05 (CD readiness) ──► needs Portainer auth (AC-07)
test_06 (suite behavior) ──► meta-tests: verifies skip-safety and idempotency
```

---

## 3. Shared Fixtures (`conftest.py`)

### 3.1 Compose Lifecycle Fixtures

```python
@pytest.fixture(scope="session")
def compose_running():
    """Check if all compose services are running. Session-scoped — checked once."""
    result = subprocess.run(
        ["docker", "compose", "-f", "compose.yaml", "ps", "--services", "--status", "running"],
        capture_output=True, text=True, timeout=10
    )
    services = result.stdout.strip().split("\n") if result.returncode == 0 else []
    return len(services) >= 4  # All services: woodpecker-server, woodpecker-agent, sonarqube, portainer

@pytest.fixture(autouse=True)
def skip_if_stack_down(compose_running):
    """Auto-skip all acceptance tests when stack is not running."""
    if not compose_running:
        pytest.skip("Compose stack not running — acceptance tests require all services up")
```

### 3.2 HTTP Helper Fixtures

```python
@pytest.fixture(scope="session")
def http_session():
    """Shared HTTP session with retry and timeout defaults."""
    import requests
    session = requests.Session()
    session.verify = False  # localhost self-signed certs
    return session

@pytest.fixture
def woodpecker_url():
    return "http://localhost:8000"

@pytest.fixture
def sonarqube_url():
    return "http://localhost:9000"  # Internal port (compose network)

@pytest.fixture
def sonarqube_external_url():
    return "http://localhost:9001"  # External mapped port

@pytest.fixture
def portainer_url():
    return "https://localhost:9443"
```

### 3.3 Authentication Token Fixtures

```python
@pytest.fixture(scope="session")
def sonarqube_token(http_session, sonarqube_url):
    """Authenticate with SonarQube default admin credentials. Session-scoped."""
    resp = http_session.post(
        f"{sonarqube_url}/api/authentication/login",
        data={"login": "admin", "password": "admin"}  # pragma: allowlist secret
    )
    assert resp.status_code == 200, f"SonarQube login failed: {resp.status_code}"
    return resp.cookies  # SonarQube uses cookie-based auth

@pytest.fixture(scope="session")
def portainer_token(http_session, portainer_url):
    """Initialize Portainer admin (if first run) and return JWT. Session-scoped."""
    # Try to initialize first-run admin
    test_password = "acceptance-test-pass-123!"  # pragma: allowlist secret
    init_resp = http_session.post(
        f"{portainer_url}/api/users/admin/init",
        json={"Username": "admin", "Password": test_password}
    )
    # If already initialized (HTTP 409), authenticate with known admin password
    if init_resp.status_code == 409:
        # Admin already initialized — authenticate
        pass  # Fall through to auth below
    elif init_resp.status_code in (200, 201):
        pass  # Init succeeded — now authenticate

    # Authenticate to get JWT
    auth_resp = http_session.post(
        f"{portainer_url}/api/auth",
        json={"Username": "admin", "Password": test_password}
    )
    assert auth_resp.status_code == 200, f"Portainer auth failed: {auth_resp.status_code}"
    data = auth_resp.json()
    assert "jwt" in data, "Portainer auth response missing JWT"
    return data["jwt"]
```

### 3.4 Pipeline Configuration Fixtures

```python
@pytest.fixture
def woodpecker_config():
    """Load .woodpecker.yml (from shared tests/conftest.py)."""
    # Reuses existing fixture from tests/conftest.py
    import yaml
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    with open(project_root / ".woodpecker.yml") as f:
        return yaml.safe_load(f)
```

---

## 4. Interface Definitions

### 4.1 Test-to-Service Interactions

| Test File | Service | Protocol | Endpoints |
|-----------|---------|----------|-----------|
| test_01 | Woodpecker | HTTP | GET `/`, GET `/healthz` |
| test_01 | SonarQube | HTTP | GET `/api/system/status`, GET `/` |
| test_01 | Portainer | HTTPS | GET `/` (UI), POST `/api/users/admin/init` |
| test_02 | Woodpecker | HTTP | GET `/api/user` (no-auth test) |
| test_02 | SonarQube | HTTP | POST `/api/authentication/login`, GET `/api/projects/search` |
| test_02 | Portainer | HTTPS | POST `/api/users/admin/init`, POST `/api/auth`, GET `/api/endpoints` |
| test_03 | (none) | File I/O | Parse `.woodpecker.yml` |
| test_04 | SonarQube | HTTP | POST `/api/projects/create`, GET `/api/projects/search`, POST `/api/projects/delete` |
| test_05 | Portainer | HTTPS | GET `/api/endpoints` (authenticated) |
| test_06 | (none) | Meta | Run twice, compare results |

### 4.2 Error Handling Contract

All HTTP tests follow this pattern:

```python
def test_something(http_session, some_url):
    try:
        resp = http_session.get(f"{some_url}/endpoint", timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    except (requests.ConnectionError, requests.Timeout) as e:
        pytest.fail(f"Connection failed: {e}")
```

Timeout: 10 seconds per request. Retries: handled by `requests.Session` adapter (3 retries, backoff).

### 4.3 Skip Contract

Every test function must either:
- Use the `skip_if_stack_down` autouse fixture (inherited)
- Or explicitly check `compose_running` before making assertions

No test may fail because the stack is not running. That is a skip, not a failure.

---

## 5. Data Flow

```
make test-acceptance
    │
    ▼
pytest tests/acceptance/
    │
    ├── conftest.py: check compose_running (docker compose ps)
    │       │
    │       ├── STACK DOWN → all tests pytest.skip
    │       │
    │       └── STACK UP → continue
    │               │
    │               ├── test_01: HTTP GET → Woodpecker, SonarQube, Portainer
    │               │   Assert: HTTP 200, expected JSON bodies
    │               │
    │               ├── test_02: HTTP POST → SonarQube login, Portainer init/auth
    │               │   Assert: valid session tokens, JWT present
    │               │
    │               ├── test_03: Read .woodpecker.yml from disk
    │               │   Assert: all steps present, correct depends_on ordering
    │               │
    │               ├── test_04: HTTP POST → SonarQube create project
    │               │   Assert: project created, then delete it
    │               │
    │               ├── test_05: HTTP GET → Portainer endpoints
    │               │   Assert: local Docker endpoint exists
    │               │
    │               └── test_06: Run test_01 twice, compare results
    │                   Assert: identical pass/fail/skip counts
    │
    └── pytest summary: passed/failed/skipped
```

---

## 6. Tradeoffs and Decisions

### Decision 1: pytest over Gherkin/BDD

| Option | Pros | Cons |
|--------|------|------|
| **pytest** (chosen) | Existing repo infrastructure, fixtures system, marker support, Makefile targets, CI integration | No Gherkin human-readable spec layer |
| Gherkin (behave/pytest-bdd) | Business-readable `.feature` files, Given/When/Then syntax | Introduces new dependency, no existing repo patterns, redundant for platform engineers |

**Rationale:** This is a platform engineering tool consumed by platform engineers. The audience
doesn't need Gherkin's business-readable layer. pytest's fixture system handles the compose-aware
lifecycle needs better than behave's environment hooks. Adding `pytest-bdd` later is possible
without throwing away pytest tests.

### Decision 2: No Selenium/Browser Automation

| Option | Pros | Cons |
|--------|------|------|
| **HTTP API only** (chosen) | Fast, deterministic, no headless browser dependency, CI-friendly | Can't test client-side JS behavior, can't verify rendered UI |
| Selenium/Playwright | Full browser testing | Slow, flaky, requires browser install in CI, overkill for API health verification |

**Rationale:** The acceptance criteria are about service availability, authentication, and
pipeline structure — all API-verifiable. UI rendering is a lower-tier concern handled by
manual testing. Adding browser tests would make the suite too slow for CI (target: < 5 min).

### Decision 3: Portainer Admin Initialization Strategy

| Option | Pros | Cons |
|--------|------|------|
| **Initialize-then-auth** (chosen) | Works on fresh stacks, handles already-initialized stacks gracefully (409 response) | Test must know the password it set |
| Skip Portainer if not initialized | No side effects | Would always skip — Portainer is useless without admin setup |

**Rationale:** Portainer requires admin initialization before any API use. The test must do
this. However, the suite must also work on a stack that already has an admin user (e.g.,
after a prior `make test-acceptance` run). The 409-fallback pattern handles both cases.

**Risk:** If someone changes the Portainer admin password between test runs, the auth
fixture will fail. Mitigation: document that the `portainer_password` secret/environment
variable must match what the test expects, or the test will fail and tell you why.

### Decision 4: Pipeline Structure via File Parsing, Not API

| Option | Pros | Cons |
|--------|------|------|
| **Parse .woodpecker.yml** (chosen) | No Woodpecker auth needed, no repo/pipeline API knowledge needed, works offline | Doesn't verify Woodpecker actually loaded the pipeline |
| Woodpecker API | Verifies Woodpecker's actual pipeline state | Requires auth, repo must exist in Woodpecker, API may not expose full step details |

**Rationale:** The acceptance criteria (AC-08, AC-09) are about pipeline structure, not
Woodpecker's runtime pipeline registry. Parsing `.woodpecker.yml` directly is sufficient
for verifying the platform's CI definition. Woodpecker API integration would add auth
complexity for a marginal gain.

---

## 7. Impacted Files

| File | Change | Reason |
|------|--------|--------|
| `tests/acceptance/conftest.py` | **NEW** | Shared fixtures for compose lifecycle, auth tokens, HTTP helpers |
| `tests/acceptance/test_01_stack_health.py` | **NEW** | AC-01 through AC-04 |
| `tests/acceptance/test_02_authentication.py` | **NEW** | AC-05 through AC-07 |
| `tests/acceptance/test_03_pipeline_structure.py` | **NEW** | AC-08, AC-09, AC-12 |
| `tests/acceptance/test_04_security_simulation.py` | **NEW** | AC-10 |
| `tests/acceptance/test_05_portainer_cd.py` | **NEW** | AC-11 |
| `tests/acceptance/test_06_suite_behavior.py` | **NEW** | AC-13, AC-14 |
| `tests/acceptance/__init__.py` | Exists | No change |
| `tests/acceptance/test_full_pipeline.py` | **MODIFIED** | Move existing tests to new structure or deprecate |
| `Makefile` | **MODIFIED** | Ensure `test-acceptance` target runs new suite |
| `tests/requirements.txt` | **MODIFIED** | Add `requests` if not already present |
| `docs/KNOWN_LIMITATIONS.md` | **MODIFIED** | Update L-007: acceptance tests now exist |
| `README.md` | **MODIFIED** | Add acceptance test suite documentation |
| `docs/specification.md` | **MODIFIED** | Update to v0.3 |
| `docs/acceptance-criteria.md` | **NEW** | Binary pass/fail criteria map |
| `docs/design.md` | **MODIFIED** | This document |

---

## 8. Constraints

- **No external test dependencies beyond `requests`.** The smoke tests use `urllib.request`
  (stdlib). Acceptance tests may use `requests` for cleaner HTTPS and session handling,
  but must not introduce heavyweight frameworks (Selenium, Playwright, pytest-bdd).
- **Must pass `make validate`.** YAML lint, shellcheck, and pre-commit hooks apply.
- **Must work in CI.** Tests that require a running stack will skip in CI (no stack available).
  Tests that parse `.woodpecker.yml` will run in CI.
- **No hardcoded credentials.** The Portainer test password is generated per session, not
  stored. SonarQube uses the well-known default `admin/admin` which is documented public
  knowledge — not a secret.
- **Portainer HTTPS.** `requests.Session.verify = False` is acceptable for localhost testing.
  Must be documented as localhost-only.

---

## 9. Architecture Decisions Record

| ADR | Decision | Rationale | Date |
|-----|----------|-----------|------|
| ADR-001 | Use pytest over Gherkin/BDD | Existing repo infrastructure, no business-stakeholder audience | 2026-07-02 |
| ADR-002 | HTTP API only, no browser automation | Speed (< 5 min), CI compatibility, ACs are API-verifiable | 2026-07-02 |
| ADR-003 | Initialize-then-auth for Portainer | Handles both fresh and pre-initialized stacks | 2026-07-02 |
| ADR-004 | Parse .woodpecker.yml for pipeline structure | No Woodpecker server auth needed, ACs are about file structure | 2026-07-02 |
| ADR-005 | `requests` library over `urllib.request` | HTTPS session handling, retry support, cleaner API for JSON POST | 2026-07-02 |
