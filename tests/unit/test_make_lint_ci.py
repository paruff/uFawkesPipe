import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent.parent
DOCKER = shutil.which("docker") is not None


def _docker_up() -> bool:
    return (
        DOCKER
        and subprocess.run(["docker", "info"], capture_output=True).returncode == 0
    )


def _lint_ci(rel_file: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["make", "lint-ci", f"LINT_CI_FILES={rel_file}"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=300,
    )


def test_lint_ci_uses_pinned_image():
    content = (REPO / "Makefile").read_text(encoding="utf-8")
    assert "woodpeckerci/woodpecker-cli:v" in content
    assert "woodpecker-cli:latest" not in content


@pytest.mark.skipif(not _docker_up(), reason="docker not available")
class TestLintCiRunsInDocker:
    def test_real_pipeline_passes(self):
        assert _lint_ci(".woodpecker.yml").returncode == 0

    def test_seeded_bad_pipeline_fails(self):
        # The target mounts the repo, so the bad file must live inside it.
        with tempfile.TemporaryDirectory(dir=REPO) as tmp:
            bad = Path(tmp) / "bad.yml"
            bad.write_text(
                "steps:\n  - name: x\n    commands: [echo hi]\n", encoding="utf-8"
            )
            assert _lint_ci(str(bad.relative_to(REPO))).returncode != 0
