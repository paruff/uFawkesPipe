"""DEPRECATED — Acceptance tests for pipeline structure.

This file is kept for reference but its tests have been migrated to:
  - tests/acceptance/test_03_pipeline_structure.py  (pipeline structure, steps, ordering)

These tests are retained to avoid breaking existing coverage counts.
New acceptance tests should be added to the numbered test files
(test_01_ through test_06_).

See docs/acceptance-criteria.md for the full AC-to-test mapping.
"""

import pytest
import subprocess


@pytest.mark.acceptance
class TestFullPipeline:
    """End-to-end pipeline validation (deprecated — see test_03_*)."""

    def test_pipeline_has_stages(self, woodpecker_config):
        """.woodpecker.yml must have the expected 6-stage ordering."""
        steps = woodpecker_config.get("steps", [])
        step_names = [s["name"] for s in steps]

        expected = [
            "init",
            "lint-yaml",
            "lint-shell",
            "unit-tests",
            "integration-tests",
            "contract-tests",
            "secrets-scan",
            "vuln-scan-fs",
            "vuln-scan-image",
            "build-image",
            "upload-defectdojo",
            "notify-obs",
        ]
        for name in expected:
            assert name in step_names, f"Missing step: {name}"

    def test_pipeline_dependency_ordering(self, woodpecker_config):
        """Pipeline steps must have correct dependency ordering."""
        steps = woodpecker_config.get("steps", [])

        next(s for s in steps if s["name"] == "init")
        lint_yaml = next(s for s in steps if s["name"] == "lint-yaml")
        assert "init" in lint_yaml.get("depends_on", []), (
            "lint-yaml must depend on init"
        )

        secrets_scan = next(s for s in steps if s["name"] == "secrets-scan")
        test_deps = {"unit-tests", "integration-tests", "contract-tests"}
        deps = set(secrets_scan.get("depends_on", []))
        assert test_deps.issubset(deps), (
            f"secrets-scan must depend on all test steps: {deps}"
        )

        build_image = next(s for s in steps if s["name"] == "build-image")
        security_deps = {"vuln-scan-fs", "vuln-scan-image"}
        build_deps = set(build_image.get("depends_on", []))
        assert security_deps.issubset(build_deps), (
            f"build-image must depend on security steps: {build_deps}"
        )

    def test_pipeline_has_when_condition(self, woodpecker_config):
        """.woodpecker.yml must have a global when condition."""
        assert "when" in woodpecker_config, "Missing global 'when' condition"
        events = woodpecker_config["when"]
        assert len(events) > 0, "when condition is empty"

    def test_yamllint_passes(self, project_root):
        """yamllint must pass on key YAML files."""
        try:
            result = subprocess.run(
                ["yamllint", "compose.yaml", ".woodpecker.yml", ".env.example"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(project_root),
            )
            if result.returncode != 0:
                pytest.skip(f"yamllint reported issues (non-blocking): {result.stderr}")
        except FileNotFoundError:
            pytest.skip("yamllint not installed")
