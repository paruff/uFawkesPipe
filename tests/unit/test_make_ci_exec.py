import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).parent.parent.parent
PILOT = REPO / "dev" / "compose.pilot.yaml"


def _docker_up() -> bool:
    return (
        shutil.which("docker") is not None
        and subprocess.run(
            ["docker", "info"], capture_output=True, check=False
        ).returncode
        == 0
    )


def _pipeline(command: str) -> str:
    return yaml.safe_dump(
        {
            "when": [{"event": "push"}],
            "steps": [{"name": "s", "image": "alpine:3.20", "commands": [command]}],
        }
    )


def _ci_exec(command: str) -> subprocess.CompletedProcess:
    # The target mounts the repo at its own path, so the pipeline must live inside it.
    with tempfile.TemporaryDirectory(dir=REPO) as tmp:
        f = Path(tmp) / "p.yml"
        f.write_text(_pipeline(command), encoding="utf-8")
        return subprocess.run(
            ["make", "ci-exec", f"CI_FILE={f.relative_to(REPO)}"],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )


def _images(path: Path) -> set[str]:
    services = yaml.safe_load(path.read_text(encoding="utf-8"))["services"]
    return {
        s["image"]
        for s in services.values()
        if s["image"].startswith("woodpeckerci/woodpecker-")
    }


def test_make_targets_exist():
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    for target in ("lint-ci", "ci-exec"):
        assert re.search(rf"^{target}:", makefile, re.MULTILINE)


def test_ci_exec_always_sets_push_event_and_ignores_secrets_file():
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    assert "--pipeline-event push" in makefile
    assert ".ci-exec-secrets.yaml" in (REPO / ".gitignore").read_text(encoding="utf-8")


def test_pilot_uses_same_pinned_versions_as_main_compose():
    pilot = _images(PILOT)
    assert pilot and pilot == _images(REPO / "compose.yaml")
    assert not any(i.endswith(":latest") for i in pilot)


def test_pilot_services_have_healthchecks():
    services = yaml.safe_load(PILOT.read_text(encoding="utf-8"))["services"]
    assert all("healthcheck" in s for s in services.values())


@pytest.mark.skipif(not _docker_up(), reason="docker not available")
class TestCiExecRunsInDocker:
    def test_push_filtered_step_runs(self):
        res = _ci_exec("echo ran-on-push")
        assert res.returncode == 0, res.stdout + res.stderr
        assert "ran-on-push" in res.stdout + res.stderr

    def test_seeded_failing_step_exits_non_zero(self):
        assert _ci_exec("exit 3").returncode != 0
