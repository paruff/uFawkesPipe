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


@pytest.mark.unit
def test_docker_socket_comes_from_env_and_state_is_on_named_volumes(service):
    volumes = service["volumes"]
    assert any(
        v.startswith("${DOCKER_SOCKET:-") and v.endswith(":/var/run/docker.sock")
        for v in volumes
    )
    assert {
        "runner-state:/opt/ufawkes-runner",
        "runner-toolcache:/opt/hostedtoolcache",
    } <= set(volumes)


@pytest.mark.unit
def test_env_example_lists_the_runner_keys_and_no_token():
    env = (ROOT / "runner" / ".env.example").read_text()
    for key in ("RUNNER_REPO_URL", "RUNNER_NAME", "RUNNER_TOKEN", "DOCKER_SOCKET"):
        assert re.search(rf"^{key}=", env, re.MULTILINE), key
    assert re.search(r"^RUNNER_TOKEN=$", env, re.MULTILINE), (
        "the example must not carry a token"
    )
