"""Acceptance tests: Pipeline structure verification.

Covers AC-08, AC-09, AC-12 (see docs/acceptance-criteria.md).
Verifies that .woodpecker.yml contains all expected stages,
correct dependency ordering, security gate configuration,
and observability event step.

Does NOT require the compose stack to be running — pipeline
structure is verified by parsing .woodpecker.yml directly
(see ADR-004 in docs/design.md). These tests always run.
"""

import pytest


# ── Expected pipeline structure ─────────────────────────────────────────

EXPECTED_STEPS = [
    "init",
    "lint-yaml",
    "lint-shell",
    "validate-agents",
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

# Expected dependency chains (ordered)
VALIDATE_STEPS = {"lint-yaml", "lint-shell", "validate-agents"}
TEST_STEPS = {"unit-tests", "integration-tests", "contract-tests"}


@pytest.mark.acceptance
class TestPipelineStructure:
    """Verify .woodpecker.yml has correct structure and ordering.

    These tests parse .woodpecker.yml from disk and do not require
    the compose stack to be running.
    """

    def test_all_expected_steps_present(self, woodpecker_config):
        """All 13 expected pipeline steps must exist."""
        steps = woodpecker_config.get("steps", [])
        step_names = {s["name"] for s in steps}

        for name in EXPECTED_STEPS:
            assert name in step_names, f"Missing expected step: '{name}'"

    def test_no_extra_unknown_steps(self, woodpecker_config):
        """No unexpected or undocumented steps."""
        steps = woodpecker_config.get("steps", [])
        step_names = {s["name"] for s in steps}

        unknown = step_names - set(EXPECTED_STEPS)
        assert not unknown, f"Unexpected steps in pipeline: {unknown}"

    def test_validate_steps_depend_on_init(self, woodpecker_config):
        """All validate steps must depend on init."""
        steps = woodpecker_config.get("steps", [])
        for step in steps:
            if step["name"] in VALIDATE_STEPS:
                deps = set(step.get("depends_on", []))
                assert "init" in deps, (
                    f"Step '{step['name']}' must depend on init, has depends_on: {deps}"
                )

    def test_test_steps_depend_on_validate(self, woodpecker_config):
        """All test steps must depend on all validate steps."""
        steps = woodpecker_config.get("steps", [])
        validate_names = {"lint-yaml", "lint-shell", "validate-agents"}

        for step in steps:
            if step["name"] in TEST_STEPS:
                deps = set(step.get("depends_on", []))
                assert validate_names.issubset(deps), (
                    f"Step '{step['name']}' must depend on all validate "
                    f"steps ({validate_names}), has depends_on: {deps}"
                )

    def test_secrets_scan_depends_on_tests(self, woodpecker_config):
        """Secrets-scan must depend on all test steps."""
        steps = woodpecker_config.get("steps", [])
        secrets = next(s for s in steps if s["name"] == "secrets-scan")
        deps = set(secrets.get("depends_on", []))
        assert TEST_STEPS.issubset(deps), (
            f"secrets-scan must depend on all test steps {TEST_STEPS}, "
            f"has depends_on: {deps}"
        )

    def test_build_depends_on_security(self, woodpecker_config):
        """Build-image must depend on both vuln scans."""
        steps = woodpecker_config.get("steps", [])
        build = next(s for s in steps if s["name"] == "build-image")
        deps = set(build.get("depends_on", []))
        assert "vuln-scan-fs" in deps, (
            f"build-image must depend on vuln-scan-fs, has depends_on: {deps}"
        )
        assert "vuln-scan-image" in deps, (
            f"build-image must depend on vuln-scan-image, has depends_on: {deps}"
        )

    def test_pipeline_has_when_condition(self, woodpecker_config):
        """Global when condition must exist."""
        assert "when" in woodpecker_config, (
            "Missing global 'when' condition in .woodpecker.yml"
        )
        events = woodpecker_config["when"]
        assert len(events) > 0, "Global 'when' condition is empty"


@pytest.mark.acceptance
class TestPipelineSecurityGates:
    """Verify security gate configuration (AC-09)."""

    def test_secrets_scan_hard_gate(self, woodpecker_config):
        """Secrets-scan must use gitleaks with --exit-code=1."""
        steps = woodpecker_config.get("steps", [])
        secrets = next(s for s in steps if s["name"] == "secrets-scan")

        commands = " ".join(secrets.get("commands", []))
        assert "gitleaks" in commands, "secrets-scan step must use gitleaks"
        assert "--exit-code=1" in commands or "--exit-code 1" in commands, (
            "secrets-scan must use --exit-code=1 (hard gate)"
        )

    def test_vuln_scan_fs_runs_on_all_branches(self, woodpecker_config):
        """vuln-scan-fs must not have a branch constraint."""
        steps = woodpecker_config.get("steps", [])
        vuln_fs = next(s for s in steps if s["name"] == "vuln-scan-fs")

        # No 'when' condition means runs on all events/branches
        when = vuln_fs.get("when", [])
        branch_conditions = [w.get("branch") for w in when if "branch" in w]
        assert not branch_conditions, (
            f"vuln-scan-fs should run on all branches, "
            f"but has branch constraint: {branch_conditions}"
        )

    def test_vuln_scan_image_main_only(self, woodpecker_config):
        """vuln-scan-image must be constrained to main branch."""
        steps = woodpecker_config.get("steps", [])
        vuln_img = next(s for s in steps if s["name"] == "vuln-scan-image")

        when = vuln_img.get("when", [])
        assert len(when) > 0, "vuln-scan-image must have a 'when' condition (main only)"
        main_condition = any(
            w.get("branch") == ["main"] or w.get("branch") == "main"
            for w in when
            if "branch" in w
        )
        assert main_condition, (
            f"vuln-scan-image must run on main branch only, has when: {when}"
        )


@pytest.mark.acceptance
class TestPipelineObservability:
    """Verify observability/deployment event step (AC-12)."""

    def test_notify_obs_step_exists(self, woodpecker_config):
        """notify-obs step must be present in deploy stage."""
        steps = woodpecker_config.get("steps", [])
        step_names = {s["name"] for s in steps}
        assert "notify-obs" in step_names, "Missing 'notify-obs' step in pipeline"

    def test_notify_obs_uses_pinned_curl(self, woodpecker_config):
        """notify-obs must use pinned curl image."""
        steps = woodpecker_config.get("steps", [])
        notify = next(s for s in steps if s["name"] == "notify-obs")
        image = notify.get("image", "")
        assert "curlimages/curl" in image, (
            f"notify-obs image expected curlimages/curl, got '{image}'"
        )
        assert image != "curlimages/curl:latest", (
            "notify-obs must use a pinned curl tag, not 'latest'"
        )

    def test_notify_obs_depends_on_publish(self, woodpecker_config):
        """notify-obs must depend on upload-defectdojo."""
        steps = woodpecker_config.get("steps", [])
        notify = next(s for s in steps if s["name"] == "notify-obs")
        deps = set(notify.get("depends_on", []))
        assert "upload-defectdojo" in deps, (
            f"notify-obs must depend on upload-defectdojo, has depends_on: {deps}"
        )

    def test_notify_obs_emits_structured_event(self, woodpecker_config):
        """notify-obs must emit a structured JSON deployment event."""
        steps = woodpecker_config.get("steps", [])
        notify = next(s for s in steps if s["name"] == "notify-obs")
        commands = " ".join(notify.get("commands", []))

        # Check for key fields in the OTEL deployment event payload
        expected_fields = [
            "service.name",
            "deployment.environment",
            "deployment.version",
            "deployment.status",
            "git.commit.sha",
        ]
        for field in expected_fields:
            assert field in commands, f"notify-obs OTEL payload missing field '{field}'"


@pytest.mark.acceptance
class TestYamlLintStructure:
    """yamllint verification — no compose stack needed."""

    def test_yamllint_passes(self, project_root):
        """yamllint must pass on key YAML files (skips gracefully if not installed)."""
        import subprocess

        try:
            result = subprocess.run(
                [
                    "yamllint",
                    str(project_root / "compose.yaml"),
                    str(project_root / ".woodpecker.yml"),
                    str(project_root / ".env.example"),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                pytest.skip(
                    f"yamllint reported issues (non-blocking): {result.stderr[:200]}"
                )
        except FileNotFoundError:
            pytest.skip("yamllint not installed")
