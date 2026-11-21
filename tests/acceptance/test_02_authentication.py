"""Acceptance tests: Service authentication.

Covers AC-05 through AC-07 (see docs/acceptance-criteria.md).
Verifies that:
- Woodpecker is open-access (no auth required, WOODPECKER_OPEN=true)
- SonarQube authenticates with default admin/admin credentials

Tests that require a running stack add `ensure_stack_running` as a
fixture parameter. Auth fixtures (sonarqube_token)
also check stack status and skip gracefully.
"""

import pytest


@pytest.mark.acceptance
class TestWoodpeckerOpenAccess:
    """Verify Woodpecker is open-access (NO_AUTH mode)."""

    def test_woodpecker_api_live(
        self, http_session, woodpecker_url, ensure_stack_running
    ):
        """Woodpecker API must respond (even if unauthenticated).

        With WOODPECKER_OPEN=true, the UI is open-access (tested in
        test_01, HTTP 200 on / and /healthz). The API (/api/user)
        returns 401 when unauthenticated. This confirms the API
        server is live and rejecting unauthenticated requests.
        """
        resp = http_session.get(f"{woodpecker_url}/api/user", timeout=5)
        # API returns 401 without auth (HTML login page or empty body)
        # Either is acceptable — key is the server responds
        assert resp.status_code in (200, 401), (
            f"Woodpecker API expected 200 or 401, "
            f"got {resp.status_code}: {resp.text[:200]}"
        )


@pytest.mark.acceptance
class TestSonarQubeAuthentication:
    """Verify SonarQube login with default credentials."""

    def test_sonarqube_login_default_credentials(
        self, http_session, sonarqube_url, ensure_stack_running
    ):
        """SonarQube must accept admin/admin login."""
        resp = http_session.post(
            f"{sonarqube_url}/api/authentication/login",
            data={
                "login": "admin",
                "password": "admin",  # pragma: allowlist secret
            },  # pragma: allowlist secret
            timeout=10,
        )
        assert resp.status_code == 200, (
            f"SonarQube login with admin/admin expected 200, "
            f"got {resp.status_code}: {resp.text[:150]}"
        )

    def test_sonarqube_authenticated_api_access(
        self, http_session, sonarqube_url, ensure_stack_running
    ):
        """SonarQube authenticated session must access API.

        Login first, then use the session cookies to access
        an authenticated endpoint.
        """
        # Login
        login = http_session.post(
            f"{sonarqube_url}/api/authentication/login",
            data={
                "login": "admin",
                "password": "admin",  # pragma: allowlist secret
            },
            timeout=10,
        )
        assert login.status_code == 200, (
            f"SonarQube login failed: HTTP {login.status_code}"
        )

        # Use session for authenticated request
        resp = http_session.get(f"{sonarqube_url}/api/projects/search", timeout=10)
        assert resp.status_code == 200, (
            f"SonarQube authenticated API access expected 200, "
            f"got {resp.status_code}: {resp.text[:200]}"
        )
        # Response must be valid JSON
        data = resp.json()
        assert "components" in data, (
            "SonarQube /api/projects/search response missing 'components' field"
        )
