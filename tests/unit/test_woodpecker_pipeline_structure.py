from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def pipeline() -> dict:
    return yaml.safe_load((REPO / ".woodpecker.yml").read_text(encoding="utf-8"))


def test_every_depends_on_names_a_declared_step(pipeline):
    names = {s["name"] for s in pipeline["steps"]}
    for step in pipeline["steps"]:
        missing = set(step.get("depends_on", [])) - names
        assert not missing, f"{step['name']} depends on undeclared {missing}"


def test_every_step_has_an_event_filter(pipeline):
    # A workflow-level when: applies to every step; otherwise each step needs its own.
    if any("event" in w for w in pipeline.get("when", [])):
        return
    unfiltered = [
        s["name"]
        for s in pipeline["steps"]
        if not any("event" in w for w in s.get("when", []))
    ]
    assert not unfiltered, unfiltered


def test_no_unpinned_latest_images(pipeline):
    assert not [s["name"] for s in pipeline["steps"] if s["image"].endswith(":latest")]


def test_pipeline_self_lint_steps_gate_the_test_stage(pipeline):
    steps = {s["name"]: s for s in pipeline["steps"]}
    lint = steps["lint-pipeline"]
    assert lint["image"].startswith("woodpeckerci/woodpecker-cli:v3.")
    assert "lint" in lint["entrypoint"]
    shell = steps["lint-pipeline-shell"]
    assert "scripts/woodpecker_shellcheck.py" in "\n".join(shell["commands"])
    for gated in ("unit-tests", "integration-tests", "contract-tests"):
        assert {"lint-pipeline", "lint-pipeline-shell"} <= set(
            steps[gated]["depends_on"]
        )


def test_cli_version_matches_compose_server():
    compose = (REPO / "compose.yaml").read_text(encoding="utf-8")
    pipeline = (REPO / ".woodpecker.yml").read_text(encoding="utf-8")
    tag = "v3.20.1"
    assert f"woodpecker-server:{tag}" in compose
    assert f"woodpecker-cli:{tag}" in pipeline
