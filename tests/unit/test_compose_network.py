"""
Automated acceptance test for WP-002: fawkes-net external network

Validates the standalone/suite split:
- Standalone (compose.yaml): no external network, uses default compose network
- Suite (compose.yaml + compose.suite.yaml): fawkes-net external network for
  platform service discovery
"""

import yaml
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def compose_config():
    """Load and parse standalone compose.yaml."""
    with open("compose.yaml", "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def suite_config():
    """Load and parse suite overlay compose.suite.yaml."""
    with open("compose.suite.yaml", "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def makefile_content():
    """Load Makefile content."""
    with open("Makefile", "r") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Standalone mode: compose.yaml must NOT reference fawkes-net
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestComposeStandalone:
    """Standalone compose.yaml must work without fawkes-net."""

    def test_standalone_has_no_fawkes_net(self, compose_config):
        """Acceptance: standalone compose.yaml does NOT declare fawkes-net."""
        networks = compose_config.get("networks", {})
        assert "fawkes-net" not in networks, (
            "Standalone compose.yaml must not declare 'fawkes-net' — "
            "it is a suite-mode-only network"
        )

    def test_standalone_no_services_use_fawkes_net(self, compose_config):
        """Acceptance: No standalone service attaches to fawkes-net."""
        services = compose_config.get("services", {})
        for name, svc in services.items():
            svc_networks = svc.get("networks", [])
            assert "fawkes-net" not in svc_networks, (
                f"Standalone service '{name}' must not attach to fawkes-net, "
                f"got networks: {svc_networks}"
            )

    def test_standalone_agent_uses_default_network(self, compose_config):
        """Acceptance: standalone woodpecker-agent does NOT set
        WOODPECKER_BACKEND_DOCKER_NETWORK (uses compose default)."""
        agent = compose_config.get("services", {}).get("woodpecker-agent", {})
        env_vars = agent.get("environment", [])
        env_str = " ".join(env_vars) if isinstance(env_vars, list) else str(env_vars)

        assert "WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net" not in env_str, (
            f"Standalone woodpecker-agent must not reference fawkes-net, got: {env_str}"
        )
        assert "WOODPECKER_BACKEND_DOCKER_NETWORK" not in env_str, (
            f"Standalone woodpecker-agent should not set "
            f"WOODPECKER_BACKEND_DOCKER_NETWORK at all (uses default network), "
            f"got: {env_str}"
        )


# ---------------------------------------------------------------------------
# Suite mode: compose.suite.yaml must declare fawkes-net
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestComposeSuiteMode:
    """Suite overlay must declare fawkes-net external network."""

    def test_suite_declares_fawkes_net(self, suite_config):
        """Acceptance: compose.suite.yaml declares fawkes-net as external network."""
        networks = suite_config.get("networks", {})
        assert "fawkes-net" in networks, (
            "compose.suite.yaml must declare 'fawkes-net' in networks section"
        )

    def test_suite_fawkes_net_is_external(self, suite_config):
        """Acceptance: suite fawkes-net has external: true."""
        networks = suite_config.get("networks", {})
        fawkes_net = networks.get("fawkes-net", {})
        assert fawkes_net.get("external") is True, (
            f"Suite fawkes-net must have external: true, got {fawkes_net}"
        )

    def test_suite_fawkes_net_has_correct_name(self, suite_config):
        """Acceptance: suite fawkes-net has name: fawkes-net."""
        networks = suite_config.get("networks", {})
        fawkes_net = networks.get("fawkes-net", {})
        assert fawkes_net.get("name") == "fawkes-net", (
            f"Suite fawkes-net must have name: fawkes-net, got {fawkes_net.get('name')}"
        )

    def test_suite_all_services_attached_to_fawkes_net(self, suite_config):
        """Acceptance: All four services attach to fawkes-net in suite mode."""
        services = suite_config.get("services", {})
        required_services = [
            "woodpecker-server",
            "woodpecker-agent",
            "sonarqube",
            "portainer",
        ]

        for service_name in required_services:
            service = services.get(service_name, {})
            svc_networks = service.get("networks", [])
            assert "fawkes-net" in svc_networks, (
                f"Suite service '{service_name}' must attach to fawkes-net, "
                f"got networks: {svc_networks}"
            )

    def test_suite_agent_has_fawkes_net_env(self, suite_config):
        """Acceptance: suite woodpecker-agent has
        WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net."""
        agent = suite_config.get("services", {}).get("woodpecker-agent", {})
        env_vars = agent.get("environment", [])
        env_str = " ".join(env_vars) if isinstance(env_vars, list) else str(env_vars)

        assert "WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net" in env_str, (
            f"Suite woodpecker-agent must have "
            f"WOODPECKER_BACKEND_DOCKER_NETWORK=fawkes-net, got: {env_str}"
        )


# ---------------------------------------------------------------------------
# Makefile targets
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMakefileNetworkTarget:
    """Validate Makefile network target and suite dependency."""

    def test_makefile_has_network_target(self, makefile_content):
        """Acceptance: Makefile has a 'network' target:
        docker network create fawkes-net || true."""
        assert "network:" in makefile_content, "Makefile must have a 'network' target"
        assert "docker network create fawkes-net" in makefile_content, (
            "network target must contain 'docker network create fawkes-net'"
        )
        assert "|| true" in makefile_content, (
            "network target must be idempotent with '|| true'"
        )

    def test_makefile_up_standalone_no_network(self, makefile_content):
        """Acceptance: standalone 'up' target does NOT depend on 'network'."""
        lines = makefile_content.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("up:"):
                # Extract prerequisite list (before comment)
                target_line = stripped.split("#")[0]
                # Remove "up:" to get prerequisites
                prereqs = (
                    target_line.split(":", 1)[1].strip() if ":" in target_line else ""
                )
                assert "network" not in prereqs, (
                    f"Standalone 'up' target must not depend on 'network', "
                    f"got prerequisites: '{prereqs}'"
                )
                return

    def test_makefile_up_suite_depends_on_network(self, makefile_content):
        """Acceptance: 'up-suite' target has 'network' as a prerequisite."""
        lines = makefile_content.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("up-suite:"):
                prereqs = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
                assert "network" in prereqs, (
                    f"'up-suite' target must have 'network' as a prerequisite, "
                    f"got: '{prereqs}'"
                )
                return
        pytest.fail("Makefile has no 'up-suite' target")
