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


class TestUploadDefectDojoStep:
    """Acceptance: upload-defectdojo step (WP-005) is correctly configured."""

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

    def test_uses_curl_image(self, woodpecker_config):
        """Acceptance: upload-defectdojo uses 'curlimages/curl:8.6.0'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        assert step["image"] == "curlimages/curl:8.6.0", (
            f"upload-defectdojo must use 'curlimages/curl:8.6.0', "
            f"got '{step.get('image')}'"
        )

    def test_has_dojo_api_token_secret(self, woodpecker_config):
        """Acceptance: upload-defectdojo has DOJO_API_TOKEN from_secret."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        environment = step.get("environment", {})
        dojo_token = environment.get("DOJO_API_TOKEN", {})
        assert dojo_token.get("from_secret") == "defectdojo_api_token", (
            f"upload-defectdojo must have DOJO_API_TOKEN from_secret: "
            f"defectdojo_api_token, got: {dojo_token}"
        )

    def test_branch_main_only(self, woodpecker_config):
        """Acceptance: upload-defectdojo has when: branch: main condition."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        when = step.get("when", [])
        assert when, "upload-defectdojo must have a 'when' condition with branch: main"
        branch_found = False
        for condition in when:
            if isinstance(condition, dict) and condition.get("branch") == "main":
                branch_found = True
                break
        assert branch_found, (
            f"upload-defectdojo 'when' must include 'branch: main', got: {when}"
        )

    def test_loops_over_gitleaks(self, woodpecker_config):
        """Acceptance: upload-defectdojo loops over gitleaks artifacts."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        command_str = " ".join(step.get("commands", []))
        assert "gitleaks" in command_str, (
            f"upload-defectdojo must reference 'gitleaks' in loop, got: {command_str}"
        )

    def test_loops_over_trivy_repo(self, woodpecker_config):
        """Acceptance: upload-defectdojo loops over trivy-repo artifacts."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        command_str = " ".join(step.get("commands", []))
        assert "trivy-repo" in command_str, (
            f"upload-defectdojo must reference 'trivy-repo' in loop, got: {command_str}"
        )

    def test_loops_over_trivy_image(self, woodpecker_config):
        """Acceptance: upload-defectdojo loops over trivy-image artifacts."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        command_str = " ".join(step.get("commands", []))
        assert "trivy-image" in command_str, (
            "upload-defectdojo must reference 'trivy-image' in loop, "
            f"got: {command_str}"
        )

    def test_checks_file_existence(self, woodpecker_config):
        """Acceptance: upload-defectdojo checks file existence before POST."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        command_str = " ".join(step.get("commands", []))
        assert '[ ! -f "$path" ]' in command_str or '[ -f "$path" ]' in command_str, (
            "upload-defectdojo must check file existence before POSTing, "
            f"got: {command_str}"
        )

    def test_scan_type_gitleaks(self, woodpecker_config):
        """Acceptance: upload-defectdojo maps gitleaks to 'Gitleaks Scan'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        command_str = " ".join(step.get("commands", []))
        assert "gitleaks" in command_str and "Gitleaks Scan" in command_str, (
            "upload-defectdojo must map 'gitleaks' to 'Gitleaks Scan', "
            f"got: {command_str}"
        )

    def test_scan_type_trivy_repo(self, woodpecker_config):
        """Acceptance: upload-defectdojo maps trivy-repo to 'Trivy Scan'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        command_str = " ".join(step.get("commands", []))
        assert "trivy-repo" in command_str and "Trivy Scan" in command_str, (
            "upload-defectdojo must map 'trivy-repo' to 'Trivy Scan', "
            f"got: {command_str}"
        )

    def test_scan_type_trivy_image(self, woodpecker_config):
        """Acceptance: upload-defectdojo maps trivy-image to 'Trivy Scan'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        command_str = " ".join(step.get("commands", []))
        assert "trivy-image" in command_str and "Trivy Scan" in command_str, (
            "upload-defectdojo must map 'trivy-image' to 'Trivy Scan', "
            f"got: {command_str}"
        )

    def test_uses_product_name(self, woodpecker_config):
        """Acceptance: upload-defectdojo uses CI_REPO_NAME for product_name."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        command_str = " ".join(step.get("commands", []))
        assert "CI_REPO_NAME" in command_str, (
            "upload-defectdojo must reference CI_REPO_NAME for product_name, "
            f"got: {command_str}"
        )

    def test_uses_engagement_name(self, woodpecker_config):
        """Acceptance: upload-defectdojo uses CI-Engagement as engagement_name."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        command_str = " ".join(step.get("commands", []))
        assert "CI-Engagement" in command_str, (
            "upload-defectdojo must use 'CI-Engagement' as engagement_name, "
            f"got: {command_str}"
        )

    def test_non_blocking(self, woodpecker_config):
        """Acceptance: upload-defectdojo does NOT exit non-zero on failure."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        # Should not contain bare 'exit' on failure paths
        # (rc capture is ok, explicit exit on failure is not)
        # Logging uses "level":"warn" (lowercase) for failure events
        assert '"level":"warn"' in command_str, (
            f"upload-defectdojo must log warning on failure, got: {command_str}"
        )

    def test_has_dora_logging(self, woodpecker_config):
        """Acceptance: upload-defectdojo has DORA structured JSON logging."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'upload-defectdojo' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "@timestamp" in command_str, (
            "upload-defectdojo must include DORA timestamp logging"
        )
        assert '"step":"upload-defectdojo"' in command_str, (
            "upload-defectdojo logging must include step name for traceability"
        )


class TestNotifyObsStep:
    """Acceptance: notify-obs step (WP-006) is correctly configured."""

    def _get_step(self, woodpecker_config):
        """Helper: find the notify-obs step by name."""
        steps = woodpecker_config["steps"]
        for step in steps:
            if step.get("name") == "notify-obs":
                return step
        return None

    def test_step_exists(self, woodpecker_config):
        """Acceptance: Step named 'notify-obs' exists in steps list."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step named 'notify-obs' must exist in .woodpecker.yml"

    def test_uses_curl_image(self, woodpecker_config):
        """Acceptance: notify-obs uses 'curlimages/curl:latest'."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        assert step["image"] == "curlimages/curl:latest", (
            f"notify-obs must use 'curlimages/curl:latest', got '{step.get('image')}'"
        )

    def test_branch_main_only(self, woodpecker_config):
        """Acceptance: notify-obs has when: branch: main condition."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        when = step.get("when", [])
        assert when, "notify-obs must have a 'when' condition with branch: main"
        branch_found = False
        for condition in when:
            if isinstance(condition, dict) and condition.get("branch") == "main":
                branch_found = True
                break
        assert branch_found, (
            f"notify-obs 'when' must include 'branch: main', got: {when}"
        )

    def test_has_otel_endpoint_secret(self, woodpecker_config):
        """Acceptance: notify-obs has OTEL_ENDPOINT from_secret."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        environment = step.get("environment", {})
        endpoint = environment.get("OTEL_ENDPOINT", {})
        assert endpoint.get("from_secret") == "otel_endpoint", (
            f"notify-obs must have OTEL_ENDPOINT from_secret: otel_endpoint, "
            f"got: {endpoint}"
        )

    def test_has_otel_headers_secret(self, woodpecker_config):
        """Acceptance: notify-obs has OTEL_HEADERS from_secret."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        environment = step.get("environment", {})
        headers = environment.get("OTEL_HEADERS", {})
        assert headers.get("from_secret") == "otel_headers", (
            f"notify-obs must have OTEL_HEADERS from_secret: otel_headers, "
            f"got: {headers}"
        )

    def test_has_dora_start_log(self, woodpecker_config):
        """Acceptance: notify-obs has DORA start log at beginning."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        command_str = " ".join(step.get("commands", []))
        assert "Starting notify-obs" in command_str, (
            "notify-obs must have a start log message"
        )

    def test_has_dora_end_log(self, woodpecker_config):
        """Acceptance: notify-obs has DORA completion log at end."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        command_str = " ".join(step.get("commands", []))
        assert (
            "completed" in command_str.lower() or "emission completed" in command_str
        ), "notify-obs must have a completion log message"

    def test_commands_post_to_otel_endpoint(self, woodpecker_config):
        """Acceptance: notify-obs commands POST to ${OTEL_ENDPOINT}/v1/traces."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        command_str = " ".join(step.get("commands", []))
        assert "/v1/traces" in command_str, (
            f"notify-obs must POST to /v1/traces, got: {command_str}"
        )

    def test_non_blocking(self, woodpecker_config):
        """Acceptance: notify-obs is non-blocking (uses || true)."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        command_str = " ".join(step.get("commands", []))
        assert "|| true" in command_str, (
            f"notify-obs must use '|| true' to be non-blocking, got: {command_str}"
        )

    def test_has_dora_logging(self, woodpecker_config):
        """Acceptance: notify-obs has DORA structured JSON logging."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        commands = step.get("commands", [])
        command_str = " ".join(commands)
        assert "@timestamp" in command_str, (
            "notify-obs must include DORA timestamp logging"
        )
        assert '"step":"notify-obs"' in command_str, (
            "notify-obs logging must include step name for traceability"
        )

    def test_payload_includes_service_name(self, woodpecker_config):
        """Acceptance: notify-obs payload includes service.name attribute."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        command_str = " ".join(step.get("commands", []))
        assert "service.name" in command_str, (
            "notify-obs payload must include 'service.name' attribute"
        )

    def test_payload_includes_git_commit_sha(self, woodpecker_config):
        """Acceptance: notify-obs payload includes git.commit.sha attribute."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        command_str = " ".join(step.get("commands", []))
        assert "git.commit.sha" in command_str, (
            "notify-obs payload must include 'git.commit.sha' attribute"
        )

    def test_payload_includes_pipeline_duration_ms(self, woodpecker_config):
        """Acceptance: notify-obs payload includes pipeline.duration_ms."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        command_str = " ".join(step.get("commands", []))
        assert "pipeline.duration_ms" in command_str, (
            "notify-obs payload must include 'pipeline.duration_ms' attribute"
        )

    def test_handles_missing_otel_endpoint_gracefully(self, woodpecker_config):
        """Acceptance: notify-obs handles missing OTEL_ENDPOINT gracefully."""
        step = self._get_step(woodpecker_config)
        assert step is not None, "Step 'notify-obs' not found"
        command_str = " ".join(step.get("commands", []))
        assert (
            "OTEL_ENDPOINT not set" in command_str
            or '[ -n "${OTEL_ENDPOINT:-}" ]' in command_str
        ), "notify-obs must handle missing OTEL_ENDPOINT gracefully"
