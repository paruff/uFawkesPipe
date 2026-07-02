"""
Automated acceptance test for WP-001: Add artifact directory init step to .woodpecker.yml

Validates that the pipeline's first step creates the required artifact directories
as specified in the acceptance criteria.
"""

import yaml
import pytest


@pytest.mark.unit
class TestArtifactDirs:
    """Validate WP-001 artifact directory initialization."""

    @pytest.fixture
    def woodpecker_config(self):
        """Load and parse .woodpecker.yml"""
        with open(".woodpecker.yml", "r") as f:
            return yaml.safe_load(f)

    def test_first_step_is_init(self, woodpecker_config):
        """Acceptance: .woodpecker.yml first step is named 'init', image 'alpine:3.20'"""
        steps = woodpecker_config.get("steps", [])
        assert len(steps) > 0, "Pipeline must have at least one step"
        first_step = steps[0]
        assert first_step.get("name") == "init", (
            f"First step must be named 'init', got '{first_step.get('name')}'"
        )
        assert first_step.get("image") == "alpine:3.20", (
            f"Init step must use image 'alpine:3.20', got '{first_step.get('image')}'"
        )

    def test_init_creates_artifact_security_dir(self, woodpecker_config):
        """Acceptance: init commands include 'mkdir -p artifacts/security'"""
        first_step = woodpecker_config["steps"][0]
        commands = first_step.get("commands", [])
        command_str = (
            " ".join(commands) if isinstance(commands, list) else str(commands)
        )
        assert "artifacts/security" in command_str, (
            f"Init commands must create 'artifacts/security', got: {command_str}"
        )

    def test_init_creates_artifact_coverage_dir(self, woodpecker_config):
        """Acceptance: init commands include 'mkdir -p artifacts/coverage'"""
        first_step = woodpecker_config["steps"][0]
        commands = first_step.get("commands", [])
        command_str = (
            " ".join(commands) if isinstance(commands, list) else str(commands)
        )
        assert "artifacts/coverage" in command_str, (
            f"Init commands must create 'artifacts/coverage', got: {command_str}"
        )

    def test_init_creates_artifact_tests_dir(self, woodpecker_config):
        """Acceptance: init commands include 'mkdir -p artifacts/tests'"""
        first_step = woodpecker_config["steps"][0]
        commands = first_step.get("commands", [])
        command_str = (
            " ".join(commands) if isinstance(commands, list) else str(commands)
        )
        assert "artifacts/tests" in command_str, (
            f"Init commands must create 'artifacts/tests', got: {command_str}"
        )

    def test_init_uses_mkdir_p(self, woodpecker_config):
        """Acceptance: init uses 'mkdir -p' for idempotent directory creation"""
        first_step = woodpecker_config["steps"][0]
        commands = first_step.get("commands", [])
        command_str = (
            " ".join(commands) if isinstance(commands, list) else str(commands)
        )
        assert "mkdir -p" in command_str, (
            f"Init must use 'mkdir -p' for idempotent creation, got: {command_str}"
        )
