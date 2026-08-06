"""Shared fixtures for uFawkesPipe acceptance test suite.

All fixtures here are session-scoped or function-scoped and designed for
binary pass/fail verification of the running uFawkesPipe stack.

Architecture decisions (ADR-002, ADR-005):
- HTTP API only — no browser automation
- `requests` library for HTTPS session handling and retry support
- Portainer HTTPS with verify=False for localhost self-signed certs

Fixture usage:
  Tests that require a running compose stack add `ensure_stack_running`
  as a parameter. Tests that don't need the stack omit it.
"""

import json
import subprocess
import time
from pathlib import Path

import pytest
import requests
import urllib3

# Suppress InsecureRequestWarning for localhost self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Project paths (composition over top-level conftest.py) ──────────────

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ── Compose lifecycle ───────────────────────────────────────────────────


@pytest.fixture
def ensure_stack_running(compose_running):
    """Skip test if compose stack is not running.

    Tests that require a running stack add this fixture as a
    parameter. Tests that parse files or check structure only
    should omit it.
    """
    if not compose_running:
        pytest.skip(
            "Compose stack not running — acceptance tests require all services up"
        )


@pytest.fixture(scope="session")
def compose_running():
    """Check that all 4 compose services are running.

    Session-scoped — checked once per test run. Returns True if
    woodpecker-server, woodpecker-agent, sonarqube, and portainer
    are all in 'running' state.
    """
    try:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(PROJECT_ROOT / "compose.yaml"),
                "ps",
                "--services",
                "--status",
                "running",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

    if result.returncode != 0:
        return False

    running = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
    required = {"woodpecker-server", "woodpecker-agent", "sonarqube", "portainer"}
    return required.issubset(running)


# ── HTTP session ────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def http_session():
    """Shared HTTP session with retries, timeouts, and TLS-verify disabled.

    Retries: 3 attempts with exponential backoff (1s, 2s, 4s).
    Timeout: 10s connect, 10s read.
    TLS: verify=False (localhost self-signed certs — acceptable for dev).
    """
    session = requests.Session()
    session.verify = False

    adapter = requests.adapters.HTTPAdapter(
        max_retries=3,
        pool_connections=1,
        pool_maxsize=1,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


# ── Service URLs ────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def woodpecker_url():
    """Woodpecker UI URL (open access, HTTP)."""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def sonarqube_url():
    """SonarQube URL (host-mapped port 9001 → container 9000).

    compose.yaml maps 9001:9000 — host access is via 9001.
    Port 9000 on the host is Woodpecker gRPC, not SonarQube.
    """
    return "http://localhost:9001"


@pytest.fixture(scope="session")
def sonarqube_external_url():
    """SonarQube external URL (host-mapped port, HTTP).

    Same as sonarqube_url — kept as alias for external access semantics.
    compose.yaml maps 9001:9000, so the host-accessible SonarQube port is 9001.
    """
    return "http://localhost:9001"


@pytest.fixture(scope="session")
def sonarqube_session():
    """Dedicated HTTP session for SonarQube API operations.

    Separate from the shared http_session to avoid cookie/auth state
    contamination with other services (Woodpecker, Portainer).
    Uses basic auth with default admin/admin credentials.

    Note: Timeout is set per-request, not on the session object.
    """
    import requests as req_lib
    import urllib3 as urllib3_lib

    urllib3_lib.disable_warnings(urllib3_lib.exceptions.InsecureRequestWarning)
    session = req_lib.Session()
    session.auth = ("admin", "admin")
    session.verify = False
    return session


@pytest.fixture(scope="session")
def portainer_url():
    """Portainer UI URL (HTTPS required)."""
    return "https://localhost:9443"


# ── Authentication tokens ───────────────────────────────────────────────


@pytest.fixture(scope="session")
def sonarqube_token(http_session, sonarqube_url, ensure_stack_running):
    """Authenticate with SonarQube default admin credentials.

    Returns the requests Session cookies (SonarQube uses cookie-based
    auth). Session-scoped — authenticated once per test run.
    """
    resp = http_session.post(
        f"{sonarqube_url}/api/authentication/login",
        data={
            "login": "admin",
            "password": "admin",  # pragma: allowlist secret
        },  # pragma: allowlist secret
        timeout=10,
    )
    assert resp.status_code == 200, f"SonarQube login failed: HTTP {resp.status_code}"
    return http_session.cookies


@pytest.fixture(scope="session")
def portainer_token(http_session, portainer_url, compose_running):
    """Initialize Portainer admin (if first run) and return JWT.

    Portainer auth flow (Portainer CE 2.39.3):
    1. First-run: POST /api/users/admin/init → HTTP 200 (user object, no JWT)
    2. Already initialized: POST /api/users/admin/init → HTTP 400/409
    3. Auth: POST /api/auth → HTTP 200 with {"jwt": "..."}

    Portainer has a security timeout that locks the API after ~5 min of
    inactivity (returns "Administrator initialization timeout").
    If this happens, restart Portainer: docker compose restart portainer

    Session-scoped — initialized once per test run.
    Skips via pytest.skip when compose stack is not running.
    """
    if not compose_running:
        pytest.skip(
            "Compose stack not running — acceptance tests require all services up"
        )
    test_password = "portainer-acceptance-2026!"  # pragma: allowlist secret
    auth_success = False

    # Step 1: Try first-run admin initialization
    init_resp = http_session.post(
        f"{portainer_url}/api/users/admin/init",
        json={"Username": "admin", "Password": test_password},
        timeout=15,
    )

    if init_resp.status_code in (200, 201):
        # First-run init succeeded — proceed to auth
        pass
    elif init_resp.status_code in (400, 409, 303):
        # Admin already initialized, or timeout lock — check body for clues
        body = init_resp.text
        if "timeout" in body.lower():
            pytest.fail(
                "Portainer security timeout detected. "
                "Restart Portainer and re-run: docker compose restart portainer\n"
                f"Init response: HTTP {init_resp.status_code} — {body[:200]}"
            )
        # Already initialized — proceed to auth step below
    else:
        pytest.fail(
            f"Portainer admin init unexpected response: HTTP {init_resp.status_code}"
            f" — {init_resp.text[:200]}"
        )

    # Step 2: Authenticate to get JWT
    if init_resp.status_code in (200, 201):
        time.sleep(2)  # Small delay after first-run init

    # Try the standard test password
    auth_resp = http_session.post(
        f"{portainer_url}/api/auth",
        json={"Username": "admin", "Password": test_password},
        timeout=15,
    )
    if auth_resp.status_code == 200:
        auth_success = True

    # Fallback: try alternative passwords from prior test runs
    if not auth_success:
        for alt_pwd in ["admin", "password"]:
            alt = http_session.post(
                f"{portainer_url}/api/auth",
                json={"Username": "admin", "Password": alt_pwd},
                timeout=10,
            )
            if alt.status_code == 200:
                auth_resp = alt
                auth_success = True
                break

    assert auth_success, (
        f"Portainer auth failed. "
        f"Init status: {init_resp.status_code}, "
        f"All auth attempts failed. "
        f"Response body: {auth_resp.text[:200]}"
    )

    data = auth_resp.json()
    assert "jwt" in data, (
        f"Portainer auth response missing 'jwt' field: {json.dumps(data)[:200]}"
    )
    return data["jwt"]


# ── Pipeline config (re-exports from top-level conftest.py) ─────────────


@pytest.fixture(scope="session")
def woodpecker_config():
    """Load .woodpecker.yml configuration (re-export from top-level conftest).

    This fixture is duplicated here so acceptance tests don't need to
    import from tests/conftest.py directly. The top-level conftest.py
    fixture is also available via pytest's upward fixture discovery.
    """
    import yaml

    woodpecker_path = PROJECT_ROOT / ".woodpecker.yml"
    with open(woodpecker_path) as f:
        return yaml.safe_load(f)
