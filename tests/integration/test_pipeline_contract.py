"""Integration tests for pipeline contract and configuration validation."""

import pytest
import yaml


class TestPipelineContractIntegration:
    """Cross-component validation of the pipeline contract."""

    def test_fawkespipe_example_is_valid_yaml(self, fawkespipe_example):
        """.fawkespipe.yml.example must be valid YAML."""
        with open(fawkespipe_example) as f:
            config = yaml.safe_load(f)
        assert config is not None, ".fawkespipe.yml.example is empty"

    def test_fawkespipe_has_app_section(self, fawkespipe_config):
        """.fawkespipe.yml.example must have an app section."""
        assert "app" in fawkespipe_config, "Missing 'app' section"

    def test_fawkespipe_has_build_section(self, fawkespipe_config):
        """.fawkespipe.yml.example must have a build section."""
        assert "build" in fawkespipe_config, "Missing 'build' section"

    def test_fawkespipe_has_stages_section(self, fawkespipe_config):
        """.fawkespipe.yml.example must have a stages section."""
        assert "stages" in fawkespipe_config, "Missing 'stages' section"

    def test_app_has_required_fields(self, fawkespipe_config):
        """app section must have name, type, language."""
        app = fawkespipe_config.get("app", {})
        assert "name" in app, "app missing 'name'"
        assert "type" in app, "app missing 'type'"
        assert "language" in app, "app missing 'language'"

    def test_build_has_builder_field(self, fawkespipe_config):
        """build section must have a builder field."""
        build = fawkespipe_config.get("build", {})
        assert "builder" in build, "build missing 'builder'"
        assert build["builder"] in ["cnb", "docker", "custom"], (
            f"Invalid builder: {build['builder']}"
        )

    def test_stages_have_required_sections(self, fawkespipe_config):
        """stages must include lint, test, sast, build, push."""
        stages = fawkespipe_config.get("stages", {})
        required = ["lint", "test", "sast", "build", "push"]
        for section in required:
            assert section in stages, f"stages missing '{section}'"

    def test_woodpecker_yml_is_valid(self, woodpecker_config):
        """.woodpecker.yml must be valid and have steps."""
        assert woodpecker_config is not None, ".woodpecker.yml is empty"
        assert "steps" in woodpecker_config, ".woodpecker.yml missing 'steps'"
        assert len(woodpecker_config["steps"]) > 0, ".woodpecker.yml has no steps"

    def test_all_examples_are_valid_yaml(self, project_root):
        """All .fawkespipe-*.yml examples must be valid YAML."""
        examples_dir = project_root / "examples"
        if not examples_dir.exists():
            pytest.skip("examples/ directory not found")
        for example_file in sorted(examples_dir.glob(".fawkespipe-*.yml")):
            with open(example_file) as f:
                config = yaml.safe_load(f)
            assert config is not None, f"{example_file.name} is empty"
            assert "app" in config, f"{example_file.name} missing 'app'"
            assert "build" in config, f"{example_file.name} missing 'build'"
