"""Smoke tests for SonarQube health verification."""

import pytest
import subprocess


@pytest.mark.smoke
class TestSonarQubeHealth:
    """Verify SonarQube is running and healthy."""

    @pytest.fixture
    def compose_running(self):
        """Check if compose stack is running."""
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", "compose.yaml", "ps", "--services"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and "sonarqube" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def test_sonarqube_status_endpoint(self, compose_running):
        """SonarQube /api/system/status must return UP."""
        if not compose_running:
            pytest.skip("Compose stack not running")
        import urllib.request
        import json

        try:
            resp = urllib.request.urlopen(
                "http://localhost:9000/api/system/status", timeout=10
            )
            assert resp.status == 200, f"Expected 200, got {resp.status}"
            data = json.loads(resp.read().decode())
            assert data.get("status") == "UP", (
                f"SonarQube status is {data.get('status')}, expected UP"
            )
        except (urllib.error.URLError, ConnectionRefusedError) as e:
            pytest.fail(f"SonarQube health check failed: {e}")

    def test_sonarqube_ui_accessible(self, compose_running):
        """SonarQube UI must be accessible."""
        if not compose_running:
            pytest.skip("Compose stack not running")
        import urllib.request

        try:
            resp = urllib.request.urlopen("http://localhost:9000", timeout=10)
            assert resp.status in (200, 302), f"Expected 200/302, got {resp.status}"
        except (urllib.error.URLError, ConnectionRefusedError) as e:
            pytest.fail(f"SonarQube UI check failed: {e}")
