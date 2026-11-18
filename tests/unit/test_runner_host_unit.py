"""runner/compose.yaml is the host unit for the ufawkes-ci runner (spec R6, ADR rules)."""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def service():
    compose = yaml.safe_load((ROOT / "runner" / "compose.yaml").read_text())
    return compose["services"]["ufawkes-ci-runner"]


@pytest.mark.unit
def test_image_is_the_ci_image_pinned_by_digest(service):
    assert re.fullmatch(
        r"ghcr\.io/paruff/ufawkes-ci@sha256:[0-9a-f]{64}", service["image"]
    )


@pytest.mark.unit
def test_runs_the_runner_entrypoint_and_restarts(service):
    assert service["entrypoint"] == "/usr/local/bin/runner.sh"
    assert service["restart"] == "unless-stopped"


@pytest.mark.unit
def test_has_a_healthcheck(service):
    assert "healthcheck" in service


@pytest.fixture(scope="module")
def proxy():
    compose = yaml.safe_load((ROOT / "runner" / "compose.yaml").read_text())
    return compose["services"]["socket-proxy"]


@pytest.mark.unit
def test_runner_reaches_docker_only_through_the_socket_proxy(service):
    assert service["environment"]["DOCKER_HOST"] == "tcp://socket-proxy:2375"
    assert not any("docker.sock" in v for v in service["volumes"]), (
        "the runner must not mount the raw socket"
    )
    assert {
        "runner-state:/opt/ufawkes-runner",
        "runner-toolcache:/opt/hostedtoolcache",
    } <= set(service["volumes"])


@pytest.mark.unit
def test_proxy_is_pinned_read_only_socket_and_limited_to_the_runner(proxy):
    assert re.search(r"socket-proxy:\d+\.\d+\.\d+@sha256:[0-9a-f]{64}", proxy["image"])
    assert any(
        v.startswith("${DOCKER_SOCKET:-") and v.endswith(":/var/run/docker.sock:ro")
        for v in proxy["volumes"]
    )
    assert "-allowfrom=ufawkes-ci-runner" in proxy["command"]
    assert not any("prune" in arg for arg in proxy["command"])


@pytest.mark.unit
def test_env_example_lists_the_runner_keys_and_no_token():
    env = (ROOT / "runner" / ".env.example").read_text()
    for key in ("RUNNER_REPO_URL", "RUNNER_NAME", "RUNNER_TOKEN", "DOCKER_SOCKET"):
        assert re.search(rf"^{key}=", env, re.MULTILINE), key
    assert re.search(r"^RUNNER_TOKEN=$", env, re.MULTILINE), (
        "the example must not carry a token"
    )


@pytest.mark.unit
def test_obs_override_joins_the_runner_to_the_external_observability_network():
    override = yaml.safe_load((ROOT / "runner" / "compose.obs.yaml").read_text())
    assert "observability-lab" in override["services"]["ufawkes-ci-runner"]["networks"]
    assert override["networks"]["observability-lab"] == {"external": True}
