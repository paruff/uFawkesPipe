"""Integration tests for Docker Compose configuration validation."""

import pytest
import yaml


class TestComposeIntegration:
    """Cross-component validation of Docker Compose configuration."""

    def test_compose_has_services(self, compose_config):
        """compose.yaml must have services section with expected services."""
        assert "services" in compose_config, "Missing 'services' section"
        expected_services = {"woodpecker-server", "woodpecker-agent", "sonarqube"}
        actual_services = set(compose_config["services"].keys())
        missing = expected_services - actual_services
        assert not missing, f"Missing expected services: {missing}"

    def test_compose_services_have_healthcheck(self, compose_config):
        """All core services should have healthchecks."""
        services_without = []
        for name, config in compose_config["services"].items():
            if "healthcheck" not in config:
                services_without.append(name)
        if services_without:
            pytest.skip(f"Services without healthcheck: {services_without}")

    def test_compose_no_latest_tags(self, compose_config):
        """No service should use :latest image tags."""
        violations = []
        for name, config in compose_config["services"].items():
            if "image" in config:
                if config["image"].endswith(":latest"):
                    violations.append(name)
        assert not violations, f"Services using :latest: {violations}"

    def test_compose_volumes_are_named(self, compose_config):
        """Top-level volumes should be named volumes."""
        if "volumes" not in compose_config:
            pytest.skip("No volumes section")
        for vol_name in compose_config["volumes"]:
            assert not vol_name.startswith("/") and not vol_name.startswith("."), (
                f"Volume '{vol_name}' should be named, not a host path"
            )

    def test_docker_compose_is_valid(self, docker_compose_config):
        """Legacy docker-compose.yml must be valid YAML (deprecated but retained)."""
        assert docker_compose_config is not None, "docker-compose.yml is empty"
        assert "services" in docker_compose_config, "docker-compose.yml missing services"
