"""Unit tests for scripts/suite-bump.sh --rewrite (ci-pipeline spec R3, one bump for the suite)."""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "suite-bump.sh"
NEW = "f" * 40
OLD = "a" * 40
OTHER = "3d3c42e5aac5ba805825da76410c181273ba90b1"


def rewrite(tmp_path, text):
    """Run the rewrite mode on a workflow file holding `text`; return (changed files, new text)."""
    f = tmp_path / "w.yml"
    f.write_text(text)
    out = subprocess.run(
        ["bash", str(SCRIPT), "--rewrite", NEW, "v9.9.9", str(f)],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.split(), f.read_text()


@pytest.mark.unit
class TestSuiteBumpRewrite:
    def test_bumps_the_sha_and_replaces_the_version_comment(self, tmp_path):
        changed, text = rewrite(
            tmp_path,
            f"    uses: paruff/uFawkesPipe/.github/workflows/reusable-lint.yml@{OLD} # v1.2.1\n",
        )
        assert changed
        assert text == (
            f"    uses: paruff/uFawkesPipe/.github/workflows/reusable-lint.yml@{NEW} # v9.9.9\n"
        )

    def test_matches_the_repo_name_in_any_case(self, tmp_path):
        _, text = rewrite(
            tmp_path,
            f"    uses: paruff/ufawkespipe/.github/workflows/reusable-build.yml@{OLD}\n",
        )
        assert f"@{NEW} # v9.9.9" in text

    def test_adds_a_comment_where_there_was_none_and_keeps_wide_spacing_out(
        self, tmp_path
    ):
        _, text = rewrite(
            tmp_path,
            f"    uses: paruff/uFawkesPipe/.github/workflows/reusable-tests.yml@{OLD}  # v1.2.1\n",
        )
        assert text.endswith(f"@{NEW} # v9.9.9\n")

    def test_leaves_other_actions_and_unrelated_files_alone(self, tmp_path):
        text_in = f"    uses: actions/checkout@{OTHER} # v7\n"
        changed, text = rewrite(tmp_path, text_in)
        assert changed == []
        assert text == text_in

    def test_bumps_every_reusable_in_a_file(self, tmp_path):
        lines = "".join(
            f"  j{i}:\n    uses: paruff/uFawkesPipe/.github/workflows/reusable-{n}.yml@{OLD}\n"
            for i, n in enumerate(["preflight", "lint", "security-scanning"])
        )
        _, text = rewrite(tmp_path, lines)
        assert text.count(f"@{NEW} # v9.9.9") == 3
        assert OLD not in text
