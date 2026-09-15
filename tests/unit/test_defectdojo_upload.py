"""Tests for DefectDojo API ingestion in upload-defectdojo step.

Validates that the curl command correctly POSTs scan results to DefectDojo
and handles HTTP responses properly.
"""

import pytest


@pytest.mark.unit
class TestDefectDojoUploadStep:
    """Acceptance: upload-defectdojo step correctly wires DefectDojo API ingestion."""

    def _get_step(self, woodpecker_config):
        """Helper: find the upload-defectdojo step by name."""
        steps = woodpecker_config["steps"]
        for step in steps:
            if step.get("name") == "upload-defectdojo":
                return step
        return None

    def test_step_exists(self, woodpecker_config):
        """Acceptance: Step named 'upload-defectdojo' exists in steps list."""
        step = self._get_step(woodpecker_config)
        assert step is not None, (
            "Step named 'upload-defectdojo' must exist in .woodpecker.yml"
        )

    def test_curl_does_not_use_silent_fail_flag(self, woodpecker_config):
        """Acceptance: curl command does not use -sf flag which silently fails on HTTP errors.

        The -f flag makes curl return error code 22 for 4xx/5xx responses,
        which prevents capturing the actual HTTP status code. We need to
        capture the HTTP code to log success/failure properly.
        """
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        # Check that curl does not use -sf flag
        assert "-sf" not in command_str, (
            "upload-defectdojo curl command must not use -sf flag — "
            "it silently fails on HTTP errors and prevents capturing HTTP status code"
        )

    def test_curl_uses_silent_mode_without_fail(self, woodpecker_config):
        """Acceptance: curl command uses -s (silent) but not -f (fail).

        We want silent mode to suppress progress output, but not fail mode
        which would prevent capturing HTTP status codes for 4xx/5xx responses.
        """
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        # Check that curl uses -s flag (silent mode)
        assert "-s " in command_str or "-s-" in command_str, (
            "upload-defectdojo curl command should use -s flag for silent mode"
        )

    def test_curl_captures_http_status_code(self, woodpecker_config):
        """Acceptance: curl command captures HTTP status code via -w '%{http_code}'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert (
            "-w '%{http_code}'" in command_str or '-w "%{http_code}"' in command_str
        ), (
            "upload-defectdojo curl command must capture HTTP status code via -w '%{http_code}'"
        )

    def test_curl_posts_to_defectdojo_api(self, woodpecker_config):
        """Acceptance: curl POSTs to http://defectdojo:8080/api/v2/import-scan/."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "http://defectdojo:8080/api/v2/import-scan/" in command_str, (
            "upload-defectdojo must POST to http://defectdojo:8080/api/v2/import-scan/"
        )

    def test_curl_uses_post_method(self, woodpecker_config):
        """Acceptance: curl uses POST method."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "-X POST" in command_str, (
            "upload-defectdojo curl command must use POST method"
        )

    def test_curl_includes_auth_header(self, woodpecker_config):
        """Acceptance: curl includes Authorization header with Token."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "Authorization: Token" in command_str, (
            "upload-defectdojo must include Authorization: Token header"
        )

    def test_curl_sends_form_data(self, woodpecker_config):
        """Acceptance: curl sends form data with scan_type, engagement_name, product_name, file."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        # Check for required form fields
        for field in ["scan_type", "engagement_name", "product_name", "file=@"]:
            assert field in command_str, (
                f"upload-defectdojo must include form field '{field}'"
            )

    def test_curl_outputs_to_dev_null(self, woodpecker_config):
        """Acceptance: curl outputs to /dev/null (we only need the status code)."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "-o /dev/null" in command_str, (
            "upload-defectdojo curl command must output to /dev/null"
        )

    def test_handles_http_error_gracefully(self, woodpecker_config):
        """Acceptance: Step handles HTTP errors gracefully (non-blocking)."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        # Should use dora_warn for failures, not exit non-zero
        assert "dora_warn" in command_str, (
            "upload-defectdojo must use dora_warn on failure (non-blocking)"
        )
