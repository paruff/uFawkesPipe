"""Host ports that collide on a shared Docker host are configurable, with today's defaults."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = yaml.safe_load((ROOT / "compose.yaml").read_text())
ENV_EXAMPLE = (ROOT / ".env.example").read_text()

# service -> {container port: (env var, default host port)}
CONFIGURABLE = {
    "woodpecker-server": {
        "8000": ("WOODPECKER_UI_PORT", "8000"),
        "9000": ("WOODPECKER_GRPC_PORT", "9000"),
    },
    "portainer": {
        "9443": ("PORTAINER_HTTPS_PORT", "9443"),
        "8000": ("PORTAINER_EDGE_PORT", "9002"),
    },
}


def _published(service: str) -> dict[str, str]:
    """Container port -> the host side of each published port, as written."""
    out = {}
    for spec in COMPOSE["services"][service]["ports"]:
        host, container = str(spec).rsplit(":", 1)
        out[container] = host
    return out


@pytest.mark.unit
@pytest.mark.parametrize("service", sorted(CONFIGURABLE))
def test_host_ports_are_env_configurable_with_todays_defaults(service):
    published = _published(service)
    for container_port, (var, default) in CONFIGURABLE[service].items():
        assert published[container_port] == "${%s:-%s}" % (var, default)


@pytest.mark.unit
def test_env_example_documents_every_port_variable():
    for ports in CONFIGURABLE.values():
        for var, default in ports.values():
            assert f"{var}={default}" in ENV_EXAMPLE, var
