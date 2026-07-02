"""Acceptance tests: Security tool simulation.

Covers AC-10 (see docs/acceptance-criteria.md).
Simulates the SAST stage by creating a SonarQube project,
verifying it exists, then cleaning up.

This demonstrates that SonarQube is ready to receive projects
from the pipeline. Tests are idempotent — they create then
immediately delete the project to leave no state.

Each test is self-contained (create → verify → delete) so
there are no cross-test state dependencies.

Uses a dedicated sonarqube_session fixture with pre-configured
basic auth to avoid cookie/auth state contamination from the
shared http_session.
"""

import pytest


TEST_PROJECT_NAME = "acceptance_test_proj"
TEST_PROJECT_KEY = "acceptance_test_proj"


@pytest.mark.acceptance
class TestSonarQubeProjectLifecycle:
    """Verify SonarQube project create/search/delete (SAST simulation).

    Each test is self-contained — creates the project, verifies it,
    then deletes it. No cross-test state dependencies.
    """

    def _delete_project(self, session, sonarqube_url):
        """Helper: delete the test project (no-op if not found)."""
        resp = session.post(
            f"{sonarqube_url}/api/projects/delete",
            data={"project": TEST_PROJECT_KEY},
            timeout=15,
        )
        # 204 = deleted, 404 = already gone — both acceptable
        assert resp.status_code in (204, 404), (
            f"Project delete expected 204/404, got {resp.status_code}: "
            f"{resp.text[:150]}"
        )
        return resp

    def test_sonarqube_create_project(
        self, sonarqube_session, sonarqube_url, ensure_stack_running
    ):
        """SonarQube must accept project creation and return correct key."""
        try:
            # Create project (auth pre-configured in session)
            resp = sonarqube_session.post(
                f"{sonarqube_url}/api/projects/create",
                data={
                    "name": TEST_PROJECT_NAME,
                    "project": TEST_PROJECT_KEY,
                },
                timeout=15,
            )
            # 200 = created, 400 = already exists (idempotent)
            assert resp.status_code in (200, 400), (
                f"Project create expected 200/400, "
                f"got {resp.status_code}: {resp.text[:200]}"
            )
            if resp.status_code == 200:
                data = resp.json()
                got_key = data.get("project", {}).get("key")
                assert got_key == TEST_PROJECT_KEY, (
                    f"Created project key mismatch: expected "
                    f"'{TEST_PROJECT_KEY}', got '{got_key}'"
                )

            # Verify in search results
            search = sonarqube_session.get(
                f"{sonarqube_url}/api/projects/search",
                params={"projects": TEST_PROJECT_KEY},
                timeout=10,
            )
            assert search.status_code == 200, (
                f"Project search expected 200, got {search.status_code}: "
                f"{search.text[:200]}"
            )
            components = search.json().get("components", [])
            project_keys = [c.get("key") for c in components]
            assert TEST_PROJECT_KEY in project_keys, (
                f"Project '{TEST_PROJECT_KEY}' not found in search results: "
                f"{project_keys}"
            )

        finally:
            # Always clean up — use a fresh session to avoid state issues
            self._delete_project(sonarqube_session, sonarqube_url)

            # Verify cleanup succeeded
            search = sonarqube_session.get(
                f"{sonarqube_url}/api/projects/search",
                params={"projects": TEST_PROJECT_KEY},
                timeout=10,
            )
            assert search.status_code == 200
            components = search.json().get("components", [])
            project_keys = [c.get("key") for c in components]
            assert TEST_PROJECT_KEY not in project_keys, (
                f"Project '{TEST_PROJECT_KEY}' still exists after deletion"
            )