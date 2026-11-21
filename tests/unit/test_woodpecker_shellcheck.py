import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).parent.parent.parent
SCRIPT = REPO / "scripts" / "woodpecker_shellcheck.py"

pytestmark = pytest.mark.skipif(
    shutil.which("shellcheck") is None, reason="shellcheck not installed"
)


def _run(tmp_path: Path, commands: list[str]) -> subprocess.CompletedProcess:
    pipeline = tmp_path / ".woodpecker.yml"
    pipeline.write_text(
        yaml.safe_dump(
            {"steps": [{"name": "s", "image": "alpine:3.20", "commands": commands}]}
        ),
        encoding="utf-8",
    )
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(pipeline)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_posix_commands_pass(tmp_path):
    assert _run(tmp_path, ['echo "hi"', ". ./env.sh"]).returncode == 0


@pytest.mark.parametrize(
    "bashism", ["source ./env.sh", '[[ -n "$X" ]] && echo y', "a=(1 2 3)"]
)
def test_seeded_bashism_is_rejected(tmp_path, bashism):
    res = _run(tmp_path, [bashism])
    assert res.returncode == 1
    assert "step 's'" in res.stdout


def test_invalid_yaml_fails_cleanly(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("steps: [", encoding="utf-8")
    res = subprocess.run(
        [sys.executable, str(SCRIPT), str(bad)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 1 and "not valid YAML" in res.stdout


def test_real_pipeline_is_clean():
    res = subprocess.run(
        [sys.executable, str(SCRIPT), str(REPO / ".woodpecker.yml")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stdout


def test_hooks_are_registered_and_pinned():
    cfg = (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "id: woodpecker-lint" in cfg and "id: woodpecker-shellcheck" in cfg
    assert "woodpecker-cli:v3." in cfg and "pyyaml==" in cfg
