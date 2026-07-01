"""Smoke tests for Woodpecker CI health verification."""

import pytest
import subprocess


@pytest.mark.smoke
class TestWoodpeckerHealth:
    """Verify Woodpecker CI is running and healthy."""

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
            return result.returncode == 0 and "woodpecker" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def test_woodpecker_health_endpoint(self, compose_running):
        """Woodpecker /healthz endpoint must return 200."""
        if not compose_running:
            pytest.skip("Compose stack not running")
        import urllib.request

        try:
            resp = urllib.request.urlopen("http://localhost:8000/healthz", timeout=5)
            assert resp.status == 200, f"Expected 200, got {resp.status}"
        except (urllib.error.URLError, ConnectionRefusedError) as e:
            pytest.fail(f"Woodpecker health check failed: {e}")

    def test_woodpecker_ui_accessible(self, compose_running):
        """Woodpecker UI must be accessible."""
        if not compose_running:
            pytest.skip("Compose stack not running")
        import urllib.request

        try:
            resp = urllib.request.urlopen("http://localhost:8000", timeout=5)
            assert resp.status == 200, f"Expected 200, got {resp.status}"
        except (urllib.error.URLError, ConnectionRefusedError) as e:
            pytest.fail(f"Woodpecker UI check failed: {e}")
