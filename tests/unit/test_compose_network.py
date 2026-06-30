"""
Automated acceptance test for WP-002: Add fawkes-net external network to compose.yaml and Makefile

Validates that the Docker Compose stack declares the fawkes-net external network
and all services are attached to it, with the Woodpecker agent configured correctly.
"""

import yaml
import pytest


class TestComposeNetwork:
    """Validate WP-002 fawkes-net external network configuration."""

    @pytest.fixture
    def compose_config(self):
        """Load and parse compose.yaml"""
        with open("compose.yaml", "r") as f:
            return yaml.safe_load(f)

    def test_fawkes_net_network_declared(self, compose_config):
        """Acceptance: compose.yaml declares fawkes-net as external network"""
        networks = compose_config.get("networks", {})
        assert "fawkes-net" in networks, (
            "compose.yaml must declare 'fawkes-net' in networks section"
        )

    def test_fawkes_net_is_external(self, compose_config):
        """Acceptance: fawkes-net has external: true"""
        networks = compose_config.get("networks", {})
        fawkes_net = networks.get("fawkes-net", {})
        assert fawkes_net.get("external") is True, (
            f"fawkes-net must have external: true, got {fawkes_net}"
        )

    def test_fawkes_net_has_correct_name(self, compose_config):
        """Acceptance: fawkes-net has name: fawkes-net"""
        networks = compose_config.get("networks", {})
        fawkes_net = networks.get("fawkes-net", {})
        assert fawkes_net.get("name") == "fawkes-net", (
            f"fawkes-net must have name: fawkes-net, got {fawkes_net.get('name')}"
        )

    def test_all_services_attached_to_fawkes_net(self, compose_config):
        """Acceptance: All four services have networks: [fawkes-net]"""
        services = compose_config.get("services", {})
        required_services = [
            "woodpecker-server",
            "woodpecker-agent",
            "sonarqube",
            "portainer",
        ]

        for service_name in required_services:
            service = services.get(service_name, {})
            networks = service.get("networks", [])
            assert "fawkes-net" in networks, (
                f"Service '{service_name}' must have networks: [fawkes-net], got {networks}"
            )

    def test_woodpecker_agent_env_var_fawkes_net(self, compose_config):
        """Acceptance: woodpecker-agent has WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net"""
        services = compose_config.get("services", {})
        agent = services.get("woodpecker-agent", {})
        env_vars = agent.get("environment", [])

        # Handle both list format (- VAR=value) and dict format (VAR: value)
        env_str = " ".join(env_vars) if isinstance(env_vars, list) else str(env_vars)

        assert "WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net" in env_str, (
            f"woodpecker-agent must have WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net, got: {env_str}"
        )

    def test_woodpecker_agent_no_longer_uses_default_network(self, compose_config):
        """Acceptance: woodpecker-agent no longer references ufawkespipe_default"""
        services = compose_config.get("services", {})
        agent = services.get("woodpecker-agent", {})
        env_vars = agent.get("environment", [])

        env_str = " ".join(env_vars) if isinstance(env_vars, list) else str(env_vars)

        assert "ufawkespipe_default" not in env_str, (
            f"woodpecker-agent must not reference ufawkespipe_default, got: {env_str}"
        )


class TestMakefileNetworkTarget:
    """Validate Makefile has network target and up target calls it."""

    @pytest.fixture
    def makefile_content(self):
        """Load Makefile content"""
        with open("Makefile", "r") as f:
            return f.read()

    def test_makefile_has_network_target(self, makefile_content):
        """Acceptance: Makefile has a 'network' target: docker network create fawkes-net || true"""
        assert "network:" in makefile_content, "Makefile must have a 'network' target"
        assert "docker network create fawkes-net" in makefile_content, (
            "network target must contain 'docker network create fawkes-net'"
        )
        assert "|| true" in makefile_content, (
            "network target must be idempotent with '|| true'"
        )

    def test_makefile_up_calls_network(self, makefile_content):
        """Acceptance: Makefile 'up' target has 'network' as a prerequisite or calls 'make network'"""
        lines = makefile_content.split("\n")
        up_calls_network = False

        for line in lines:
            if line.strip().startswith("up:"):
                # Check prerequisites on the up: line itself (e.g., "up: network")
                if "network" in line.split("#")[0]:  # ignore comment after ##
                    up_calls_network = True
                # Also check recipe lines below
                in_up_target = True
                continue

        # If not found in prerequisites, check recipe lines
        if not up_calls_network:
            in_up_target = False
            for line in lines:
                if line.strip().startswith("up:"):
                    in_up_target = True
                    continue
                if in_up_target and line.startswith("\t"):
                    if "make network" in line or "$(MAKE) network" in line:
                        up_calls_network = True
                elif in_up_target and line and not line.startswith("\t"):
                    break

        assert up_calls_network, (
            "Makefile 'up' target must have 'network' as a prerequisite or call 'make network'"
        )
