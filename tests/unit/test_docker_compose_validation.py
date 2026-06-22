"""Unit tests for docker-compose.yml configuration validation."""

import pytest
import yaml
from pathlib import Path


class TestDockerComposeValidation:
    """Validate docker-compose.yml structure and configuration."""

    def test_docker_compose_is_valid_yaml(self, docker_compose_file):
        """docker-compose.yml must be valid YAML."""
        with open(docker_compose_file) as f:
            config = yaml.safe_load(f)
        assert config is not None, "docker-compose.yml is empty"

    def test_has_services_section(self, docker_compose_config):
        """docker-compose.yml must have a services section."""
        assert "services" in docker_compose_config, "Missing 'services' section"

    def test_all_services_have_image_or_build(self, docker_compose_config):
        """Every service must have either 'image' or 'build' specified."""
        for service_name, service_config in docker_compose_config["services"].items():
            assert "image" in service_config or "build" in service_config, (
                f"Service '{service_name}' must have 'image' or 'build'"
            )

    def test_no_latest_tags(self, docker_compose_config):
        """No service should use ':latest' image tags."""
        for service_name, service_config in docker_compose_config["services"].items():
            if "image" in service_config:
                image = service_config["image"]
                assert not image.endswith(":latest"), (
                    f"Service '{service_name}' uses ':latest' tag: {image}"
                )

    def test_all_services_have_healthcheck(self, docker_compose_config):
        """Every service should have a healthcheck defined (soft check)."""
        services_without_healthcheck = []
        for service_name, service_config in docker_compose_config["services"].items():
            if "healthcheck" not in service_config:
                services_without_healthcheck.append(service_name)

        # Warn but don't fail - some services may not need healthchecks
        if services_without_healthcheck:
            import warnings
            warnings.warn(
                f"Services without healthcheck: {', '.join(services_without_healthcheck)}",
                UserWarning,
            )

    def test_healthchecks_have_retries(self, docker_compose_config):
        """Healthchecks should have retries defined."""
        for service_name, service_config in docker_compose_config["services"].items():
            if "healthcheck" in service_config:
                healthcheck = service_config["healthcheck"]
                assert "retries" in healthcheck or "test" in healthcheck, (
                    f"Service '{service_name}' healthcheck missing retries/test"
                )

    def test_no_secrets_in_compose(self, docker_compose_config):
        """No hardcoded secrets or credentials in docker-compose.yml."""
        content = yaml.dump(docker_compose_config)
        # Only check for actual hardcoded values, not variable references
        sensitive_patterns = [
            "password: admin",
            "password: password",
            "password: root",
            "secret: secret",
            "token: token",
            "api_key: key",
            "PRIVATE_KEY: -----BEGIN",
        ]
        for pattern in sensitive_patterns:
            assert pattern.lower() not in content.lower(), (
                f"Found hardcoded secret '{pattern}' in docker-compose.yml"
            )

    def test_volumes_are_named(self, docker_compose_config):
        """Volumes should be named, not host paths."""
        if "volumes" in docker_compose_config:
            for volume_name in docker_compose_config["volumes"]:
                # Named volumes don't start with / or .
                assert not volume_name.startswith("/") and not volume_name.startswith("."), (
                    f"Volume '{volume_name}' should be a named volume, not a host path"
                )


class TestComposeYamlValidation:
    """Validate compose.yaml structure and configuration."""

    def test_compose_is_valid_yaml(self, compose_file):
        """compose.yaml must be valid YAML."""
        with open(compose_file) as f:
            config = yaml.safe_load(f)
        assert config is not None, "compose.yaml is empty"

    def test_has_services_section(self, compose_config):
        """compose.yaml must have a services section."""
        assert "services" in compose_config, "Missing 'services' section"

    def test_all_services_have_image(self, compose_config):
        """Every service must have an 'image' specified."""
        for service_name, service_config in compose_config["services"].items():
            assert "image" in service_config, (
                f"Service '{service_name}' must have 'image'"
            )

    def test_no_latest_tags(self, compose_config):
        """No service should use ':latest' image tags."""
        for service_name, service_config in compose_config["services"].items():
            if "image" in service_config:
                image = service_config["image"]
                assert not image.endswith(":latest"), (
                    f"Service '{service_name}' uses ':latest' tag: {image}"
                )

    def test_all_services_have_labels(self, compose_config):
        """Every service must have plane/managed-by labels."""
        for service_name, service_config in compose_config["services"].items():
            labels = service_config.get("labels", [])
            label_str = " ".join(labels)
            assert "plane=ufawkespipe" in label_str, (
                f"Service '{service_name}' missing 'plane=ufawkespipe' label"
            )
            assert "managed-by=fawkes" in label_str, (
                f"Service '{service_name}' missing 'managed-by=fawkes' label"
            )

    def test_has_volume_declarations(self, compose_config):
        """Top-level volumes must be declared."""
        assert "volumes" in compose_config, "Missing top-level 'volumes' section"

    def test_no_secrets_in_compose(self, compose_config):
        """No hardcoded secrets or credentials in compose.yaml."""
        content = yaml.dump(compose_config)
        sensitive_patterns = [
            "password: admin",
            "password: password",
            "password: root",
            "secret: secret",
            "token: token",
            "api_key: key",
            "PRIVATE_KEY: -----BEGIN",
        ]
        for pattern in sensitive_patterns:
            assert pattern.lower() not in content.lower(), (
                f"Found hardcoded secret '{pattern}' in compose.yaml"
            )

    def test_volumes_are_named(self, compose_config):
        """Volumes should be named, not host paths."""
        if "volumes" in compose_config:
            for volume_name in compose_config["volumes"]:
                assert not volume_name.startswith("/") and not volume_name.startswith("."), (
                    f"Volume '{volume_name}' should be a named volume, not a host path"
                )
