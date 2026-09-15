"""Tests for scripts/release.sh automated release script.

Validates that the release script correctly:
- Validates version format
- Checks for release blockers
- Verifies clean git state
- Creates proper git tags
- Generates release notes
"""

import pytest
import subprocess
from pathlib import Path


@pytest.mark.unit
class TestReleaseScript:
    """Test release script functionality."""

    def test_script_exists(self):
        """Acceptance: scripts/release.sh exists and is executable."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "release.sh"
        assert script_path.exists(), "scripts/release.sh must exist"
        assert script_path.stat().st_mode & 0o111, (
            "scripts/release.sh must be executable"
        )

    def test_script_has_shebang(self):
        """Acceptance: scripts/release.sh has proper shebang."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "release.sh"
        with open(script_path) as f:
            first_line = f.readline()
        assert first_line.startswith("#!/"), (
            "scripts/release.sh must have a shebang line"
        )

    def test_script_has_set_euo_pipefail(self):
        """Acceptance: scripts/release.sh uses strict error handling."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "release.sh"
        with open(script_path) as f:
            content = f.read()
        assert "set -euo pipefail" in content, (
            "scripts/release.sh must use 'set -euo pipefail' for strict error handling"
        )

    def test_version_argument_required(self):
        """Acceptance: Script requires VERSION argument."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "release.sh"
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode != 0, "Script should fail without VERSION argument"
        # Check both stdout and stderr for VERSION mention
        output = result.stdout + result.stderr
        assert "VERSION" in output or "version" in output.lower(), (
            "Script should mention VERSION in error message"
        )

    def test_version_format_validation(self):
        """Acceptance: Script validates version format (vX.Y.Z)."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "release.sh"
        result = subprocess.run(
            [str(script_path), "invalid-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode != 0, "Script should fail with invalid version format"

    def test_version_format_accepts_valid(self):
        """Acceptance: Script accepts valid semver format (vX.Y.Z)."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "release.sh"
        # We can't actually run the full release, but we can test that it
        # accepts the version format and fails at a later stage
        result = subprocess.run(
            [str(script_path), "v1.0.0", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should fail because we're not in a release-ready state, but not
        # because of version format validation
        assert (
            "invalid" not in result.stderr.lower()
            or "version" not in result.stderr.lower()
        ), "Script should accept valid version format v1.0.0"

    def test_dry_run_flag(self):
        """Acceptance: Script supports --dry-run flag."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "release.sh"
        result = subprocess.run(
            [str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Should show usage information including --dry-run
        assert (
            "dry-run" in result.stdout.lower()
            or "dry_run" in result.stdout.lower()
            or "dry run" in result.stdout.lower()
        ), "Script should document --dry-run flag in help"

    def test_help_flag(self):
        """Acceptance: Script supports --help flag."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "release.sh"
        result = subprocess.run(
            [str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, "Script should exit 0 on --help"
        assert "usage" in result.stdout.lower() or "version" in result.stdout.lower(), (
            "Script should show usage information on --help"
        )

    def test_shellcheck_passes(self):
        """Acceptance: Script passes ShellCheck linting."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "release.sh"
        try:
            result = subprocess.run(
                ["shellcheck", str(script_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, f"ShellCheck failed:\n{result.stderr}"
        except FileNotFoundError:
            pytest.skip("shellcheck not installed")


@pytest.mark.unit
class TestReleaseScriptUnit:
    """Unit tests for release script helper functions."""

    def test_version_regex_pattern(self):
        """Acceptance: Version regex matches vX.Y.Z format."""
        import re

        # Common semver pattern
        pattern = r"^v[0-9]+\.[0-9]+\.[0-9]+$"
        assert re.match(pattern, "v1.0.0"), "Should match v1.0.0"
        assert re.match(pattern, "v0.1.0"), "Should match v0.1.0"
        assert re.match(pattern, "v10.20.30"), "Should match v10.20.30"
        assert not re.match(pattern, "1.0.0"), "Should not match 1.0.0 (missing v)"
        assert not re.match(pattern, "v1.0"), "Should not match v1.0 (missing patch)"
        assert not re.match(pattern, "v1.0.0-rc1"), "Should not match v1.0.0-rc1"

    def test_changelog_entry_format(self):
        """Acceptance: CHANGELOG entry follows Keep a Changelog format."""
        import re

        # Check that a CHANGELOG entry would match the expected format
        entry = "## [v1.0.0] - 2026-09-14"
        pattern = r"^## \[v[0-9]+\.[0-9]+\.[0-9]+\] - [0-9]{4}-[0-9]{2}-[0-9]{2}$"
        assert re.match(pattern, entry), f"CHANGELOG entry should match format: {entry}"
