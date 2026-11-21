import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent.parent
SCRIPT = REPO / "scripts" / "woodpecker-lint.sh"


def _docker_up() -> bool:
    return (
        shutil.which("docker") is not None
        and subprocess.run(
            ["docker", "info"], capture_output=True, check=False
        ).returncode
        == 0
    )


def test_hook_does_not_bind_mount_the_workspace():
    # In CI the hook runs inside a job container; the host's Docker daemon cannot see
    # the container's $PWD, so `-v $PWD:...` arrives empty ("stat .woodpecker.yml:
    # no such file"). Files must be copied in instead.
    body = SCRIPT.read_text(encoding="utf-8")
    assert "docker cp" in body
    assert " -v " not in body and "--volume" not in body
    cfg = (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "scripts/woodpecker-lint.sh" in cfg
    assert '-v "$PWD' not in cfg


@pytest.mark.skipif(not _docker_up(), reason="docker not available")
class TestLintRunsFromAnyDirectory:
    def _run(self, cwd: Path, name: str):
        return subprocess.run(
            [str(SCRIPT), name], cwd=cwd, capture_output=True, text=True, check=False
        )

    def test_real_pipeline_passes_from_a_foreign_directory(self, tmp_path):
        shutil.copy(REPO / ".woodpecker.yml", tmp_path / ".woodpecker.yml")
        res = self._run(tmp_path, ".woodpecker.yml")
        assert res.returncode == 0, res.stdout + res.stderr

    def test_seeded_bad_pipeline_fails(self, tmp_path):
        (tmp_path / "bad.yml").write_text(
            "steps:\n  - name: x\n    commands: [echo hi]\n", encoding="utf-8"
        )
        assert self._run(tmp_path, "bad.yml").returncode != 0
