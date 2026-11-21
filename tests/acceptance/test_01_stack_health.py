"""Acceptance tests: Stack health verification.

Covers AC-01 through AC-04 (see docs/acceptance-criteria.md).
Verifies that all 4 compose services are accessible on their expected
ports and respond to health/status endpoints.

Tests that require a running stack add `ensure_stack_running` as a
fixture parameter — this skips gracefully when the stack is not running.
"""

import pytest


@pytest.mark.acceptance
class TestStackHealth:
    """Verify all uFawkesPipe services are running and healthy."""

    # ── Woodpecker ─────────────────────────────────────────────────────

    def test_woodpecker_ui_accessible(
        self, http_session, woodpecker_url, ensure_stack_running
    ):
        """Woodpecker UI must return HTTP 200 on port 8000."""
        resp = http_session.get(f"{woodpecker_url}/", timeout=5)
        assert resp.status_code == 200, (
            f"Woodpecker UI expected 200, got {resp.status_code}"
        )

    def test_woodpecker_healthz(
        self, http_session, woodpecker_url, ensure_stack_running
    ):
        """Woodpecker /healthz must return 200 or 204."""
        resp = http_session.get(f"{woodpecker_url}/healthz", timeout=5)
        assert resp.status_code in (200, 204), (
            f"Woodpecker /healthz expected 200/204, got {resp.status_code}"
        )

    # ── SonarQube ──────────────────────────────────────────────────────

    def test_sonarqube_status_up(
        self, http_session, sonarqube_url, ensure_stack_running
    ):
        """SonarQube /api/system/status must return status=UP."""
        resp = http_session.get(f"{sonarqube_url}/api/system/status", timeout=10)
        assert resp.status_code == 200, (
            f"SonarQube status expected 200, got {resp.status_code}"
        )
        data = resp.json()
        assert data.get("status") == "UP", (
            f"SonarQube status expected 'UP', got '{data.get('status')}'"
        )

    def test_sonarqube_ui_accessible(
        self, http_session, sonarqube_url, ensure_stack_running
    ):
        """SonarQube UI must be accessible (200 or 302 redirect)."""
        resp = http_session.get(f"{sonarqube_url}/", timeout=10)
        assert resp.status_code in (200, 302), (
            f"SonarQube UI expected 200/302, got {resp.status_code}"
        )

    # ── Arcane (optional ``ui`` profile) ───────────────────────────────

    def test_arcane_ui_accessible(
        self, http_session, arcane_url, ensure_ui_profile_running
    ):
        """Arcane UI must return HTTP 200 on port 3552."""
        resp = http_session.get(f"{arcane_url}/", timeout=10)
        assert resp.status_code == 200, (
            f"Arcane UI expected 200, got {resp.status_code}"
        )

    # ── Service count ──────────────────────────────────────────────────

    def test_all_services_running(self, ensure_stack_running, compose_running):
        """All 3 default compose services must report 'running' status."""
        assert compose_running is True, (
            "Not all compose services are running. "
            "Run 'docker compose -f compose.yaml ps --status running' to check."
        )


@pytest.mark.acceptance
class TestStackHealthEdgeCases:
    """Edge cases: ensure_stack_running behavior."""

    def test_ensure_stack_running_works(self, ensure_stack_running):
        """Fixture passes when stack is up.

        If the stack is down, pytest.skip is raised instead of failing.
        This test verifies the fixture works — if we reach here,
        the stack is running.
        """
