"""Tests for .woodpecker.yml pipeline structure.

Validates step ordering, image pinning, and required commands
for the v0.2 pipeline specification.
"""

import pytest


class TestWoodpeckerYamlValid:
    """Basic structural validation of .woodpecker.yml."""

    def test_is_valid_yaml(self, woodpecker_config):
        """Acceptance: .woodpecker.yml parses as valid YAML."""
        assert woodpecker_config is not None

    def test_has_steps_section(self, woodpecker_config):
        """Acceptance: .woodpecker.yml has a steps list."""
        assert "steps" in woodpecker_config
        assert isinstance(woodpecker_config["steps"], list)
        assert len(woodpecker_config["steps"]) > 0

    def test_has_when_section(self, woodpecker_config):
        """Acceptance: .woodpecker.yml has a when section."""
        assert "when" in woodpecker_config


class TestStepOrdering:
    """Acceptance: Pipeline steps are in the correct order per v0.2 spec."""

    def test_first_step_is_init(self, woodpecker_config):
        """Acceptance: First step (index 0) is 'init'."""
        steps = woodpecker_config["steps"]
        assert steps[0]["name"] == "init", (
            f"Step at index 0 must be 'init', got '{steps[0]['name']}'"
        )

    def test_second_step_is_secrets_scan(self, woodpecker_config):
        """Acceptance: Second step (index 1) is 'secrets-scan'."""
        steps = woodpecker_config["steps"]
        assert steps[1]["name"] == "secrets-scan", (
            f"Step at index 1 must be 'secrets-scan', got '{steps[1]['name']}'"
        )

    def test_secrets_scan_before_lint_yaml(self, woodpecker_config):
        """Acceptance: 'secrets-scan' appears before 'lint-yaml' in step list."""
        steps = woodpecker_config["steps"]
        names = [s["name"] for s in steps]
        pos_secrets = names.index("secrets-scan")
        pos_lint_yaml = names.index("lint-yaml")
        assert pos_secrets < pos_lint_yaml, (
            f"'secrets-scan' at index {pos_secrets} must come before "
            f"'lint-yaml' at index {pos_lint_yaml}"
        )


class TestSecretsScanStep:
    """Acceptance: secrets-scan step is correctly configured."""

    def test_uses_correct_image(self, woodpecker_config):
        """Acceptance: secrets-scan uses 'zricethezav/gitleaks:v8.18.2'."""
        steps = woodpecker_config["steps"]
        step = steps[1]
        assert step["image"] == "zricethezav/gitleaks:v8.18.2", (
            f"secrets-scan must use 'zricethezav/gitleaks:v8.18.2', "
            f"got '{step.get('image')}'"
        )

    def test_has_exit_code_one_flag(self, woodpecker_config):
        """Acceptance: secrets-scan command includes '--exit-code=1'."""
        steps = woodpecker_config["steps"]
        commands = steps[1].get("commands", [])
        command_str = " ".join(commands)
        assert "--exit-code=1" in command_str, (
            f"secrets-scan must include '--exit-code=1', got: {command_str}"
        )

    def test_has_json_report_output(self, woodpecker_config):
        """Acceptance: secrets-scan writes JSON report to artifacts/security/."""
        steps = woodpecker_config["steps"]
        commands = steps[1].get("commands", [])
        command_str = " ".join(commands)
        assert (
            "--report-format=json" in command_str
        ), f"secrets-scan must use '--report-format=json', got: {command_str}"
        assert (
            "--report-path=artifacts/security/gitleaks.json" in command_str
        ), (
            f"secrets-scan must write to 'artifacts/security/gitleaks.json', "
            f"got: {command_str}"
        )

    def test_has_dora_logging(self, woodpecker_config):
        """Acceptance: secrets-scan has DORA structured JSON logging."""
        steps = woodpecker_config["steps"]
        commands = steps[1].get("commands", [])
        command_str = " ".join(commands)
        assert "@timestamp" in command_str, (
            "secrets-scan must include DORA timestamp logging"
        )
        assert '"step":"secrets-scan"' in command_str, (
            "secrets-scan logging must include step name for traceability"
        )

    def test_image_is_pinned(self, woodpecker_config):
        """Acceptance: secrets-scan image tag is pinned (not 'latest')."""
        steps = woodpecker_config["steps"]
        image = steps[1].get("image", "")
        assert "latest" not in image, (
            f"secrets-scan image must be pinned, got '{image}'"
        )
        assert ":" in image, (
            f"secrets-scan image must have a tag, got '{image}'"
        )


class TestInitStep:
    """Acceptance: init step (WP-001) is correctly configured."""

    def test_uses_correct_image(self, woodpecker_config):
        """Acceptance: init uses 'alpine:3.20'."""
        steps = woodpecker_config["steps"]
        step = steps[0]
        assert step["image"] == "alpine:3.20", (
            f"init step must use 'alpine:3.20', got '{step.get('image')}'"
        )

    def test_creates_artifact_directories(self, woodpecker_config):
        """Acceptance: init commands create the three artifact directories."""
        steps = woodpecker_config["steps"]
        commands = steps[0].get("commands", [])
        command_str = " ".join(commands)
        for d in ["artifacts/security", "artifacts/coverage", "artifacts/tests"]:
            assert d in command_str, (
                f"init must create '{d}', got: {command_str}"
            )
