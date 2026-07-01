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
        assert "--report-format=json" in command_str, (
            f"secrets-scan must use '--report-format=json', got: {command_str}"
        )
        assert "--report-path=artifacts/security/gitleaks.json" in command_str, (
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
        assert ":" in image, f"secrets-scan image must have a tag, got '{image}'"


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
            assert d in command_str, f"init must create '{d}', got: {command_str}"


class TestVulnScanFsStep:
    """Acceptance: vuln-scan-fs step (WP-004) is correctly configured."""

    def _get_step(self, woodpecker_config):
        """Helper: find the vuln-scan-fs step by name."""
        steps = woodpecker_config["steps"]
        for step in steps:
            if step.get("name") == "vuln-scan-fs":
                return step
        return None

    def test_step_exists(self, woodpecker_config):
        """Acceptance: Step named 'vuln-scan-fs' exists in steps list."""
        step = self._get_step(woodpecker_config)
        assert step is not None, (
            "Step named 'vuln-scan-fs' must exist in .woodpecker.yml"
        )

    def test_uses_trivy_latest(self, woodpecker_config):
        """Acceptance: vuln-scan-fs uses 'aquasec/trivy:latest'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-fs' not found"
        assert step["image"] == "aquasec/trivy:latest", (
            f"vuln-scan-fs must use 'aquasec/trivy:latest', got '{step.get('image')}'"
        )

    def test_has_json_format_output(self, woodpecker_config):
        """Acceptance: vuln-scan-fs command includes '--format json'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-fs' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "--format json" in command_str, (
            f"vuln-scan-fs must include '--format json', got: {command_str}"
        )

    def test_output_path(self, woodpecker_config):
        """Acceptance: vuln-scan-fs writes to artifacts/security/trivy-repo.json."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-fs' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "--output artifacts/security/trivy-repo.json" in command_str, (
            f"vuln-scan-fs must write to 'artifacts/security/trivy-repo.json', "
            f"got: {command_str}"
        )

    def test_has_no_progress(self, woodpecker_config):
        """Acceptance: vuln-scan-fs command includes '--no-progress'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-fs' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "--no-progress" in command_str, (
            f"vuln-scan-fs must include '--no-progress', got: {command_str}"
        )

    def test_scans_current_dir(self, woodpecker_config):
        """Acceptance: vuln-scan-fs scans current directory ('.')."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-fs' not found"
        commands = step.get("commands", [])
        for cmd in commands:
            if "trivy fs" in cmd:
                # The '.' scan target appears before the && rc=$? pattern
                assert " --no-progress ." in cmd, (
                    f"vuln-scan-fs trivy command must include ' --no-progress .' "
                    f"as the scan target, got: {cmd}"
                )
                return
        pytest.fail("No 'trivy fs' command found in vuln-scan-fs step")

    def test_no_branch_restriction(self, woodpecker_config):
        """Acceptance: vuln-scan-fs has NO when: branch restriction."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-fs' not found"
        assert "when" not in step, (
            "vuln-scan-fs must have NO 'when' condition — "
            "it runs on every push and pull request"
        )

    def test_no_hard_gate_exit_code(self, woodpecker_config):
        """Acceptance: vuln-scan-fs does NOT use '--exit-code 1'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-fs' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "--exit-code 1" not in command_str, (
            "vuln-scan-fs must NOT include '--exit-code 1' — "
            "findings go to DefectDojo, not a pipeline gate at v0.2"
        )

    def test_has_dora_logging(self, woodpecker_config):
        """Acceptance: vuln-scan-fs has DORA structured JSON logging."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-fs' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "@timestamp" in command_str, (
            "vuln-scan-fs must include DORA timestamp logging"
        )
        assert '"step":"vuln-scan-fs"' in command_str, (
            "vuln-scan-fs logging must include step name for traceability"
        )

    def test_security_scan_removed(self, woodpecker_config):
        """Acceptance: Old 'security-scan' step is removed."""
        steps = woodpecker_config["steps"]
        names = [s.get("name") for s in steps]
        assert "security-scan" not in names, (
            "Old 'security-scan' step must be removed — "
            "replaced by 'vuln-scan-fs' and 'vuln-scan-image'"
        )


class TestVulnScanImageStep:
    """Acceptance: vuln-scan-image step (WP-004) is correctly configured."""

    def _get_step(self, woodpecker_config):
        """Helper: find the vuln-scan-image step by name."""
        steps = woodpecker_config["steps"]
        for step in steps:
            if step.get("name") == "vuln-scan-image":
                return step
        return None

    def test_step_exists(self, woodpecker_config):
        """Acceptance: Step named 'vuln-scan-image' exists in steps list."""
        step = self._get_step(woodpecker_config)
        assert step is not None, (
            "Step named 'vuln-scan-image' must exist in .woodpecker.yml"
        )

    def test_uses_trivy_latest(self, woodpecker_config):
        """Acceptance: vuln-scan-image uses 'aquasec/trivy:latest'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-image' not found"
        assert step["image"] == "aquasec/trivy:latest", (
            f"vuln-scan-image must use 'aquasec/trivy:latest', "
            f"got '{step.get('image')}'"
        )

    def test_has_json_format_output(self, woodpecker_config):
        """Acceptance: vuln-scan-image command includes '--format json'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-image' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "--format json" in command_str, (
            f"vuln-scan-image must include '--format json', got: {command_str}"
        )

    def test_output_path(self, woodpecker_config):
        """Acceptance: vuln-scan-image writes to artifacts/security/trivy-image.json."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-image' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "--output artifacts/security/trivy-image.json" in command_str, (
            f"vuln-scan-image must write to 'artifacts/security/trivy-image.json', "
            f"got: {command_str}"
        )

    def test_has_no_progress(self, woodpecker_config):
        """Acceptance: vuln-scan-image command includes '--no-progress'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-image' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "--no-progress" in command_str, (
            f"vuln-scan-image must include '--no-progress', got: {command_str}"
        )

    def test_branch_main_only(self, woodpecker_config):
        """Acceptance: vuln-scan-image has when: branch: main condition."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-image' not found"
        when = step.get("when", [])
        assert when, "vuln-scan-image must have a 'when' condition with branch: main"
        branch_found = False
        for condition in when:
            if isinstance(condition, dict) and condition.get("branch") == "main":
                branch_found = True
                break
        assert branch_found, (
            f"vuln-scan-image 'when' must include 'branch: main', got: {when}"
        )

    def test_uses_registry_username_secret(self, woodpecker_config):
        """Acceptance: vuln-scan-image has REGISTRY_USERNAME from_secret."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-image' not found"
        environment = step.get("environment", {})
        reg_user = environment.get("REGISTRY_USERNAME", {})
        assert reg_user.get("from_secret") == "registry_username", (
            f"vuln-scan-image must have REGISTRY_USERNAME from_secret, got: {reg_user}"
        )

    def test_image_ref_uses_ci_variables(self, woodpecker_config):
        """Acceptance: vuln-scan-image references CI_REPO_NAME and CI_COMMIT_SHA."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-image' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "CI_REPO_NAME" in command_str, (
            "vuln-scan-image must reference CI_REPO_NAME for image name, "
            f"got: {command_str}"
        )
        assert "CI_COMMIT_SHA" in command_str, (
            "vuln-scan-image must reference CI_COMMIT_SHA for image tag, "
            f"got: {command_str}"
        )

    def test_has_dora_logging(self, woodpecker_config):
        """Acceptance: vuln-scan-image has DORA structured JSON logging."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'vuln-scan-image' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "@timestamp" in command_str, (
            "vuln-scan-image must include DORA timestamp logging"
        )
        assert '"step":"vuln-scan-image"' in command_str, (
            "vuln-scan-image logging must include step name for traceability"
        )
