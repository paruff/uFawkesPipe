import re
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
DOC = (REPO / "docs" / "DEVELOPING.md").read_text(encoding="utf-8")


def test_exactly_three_make_commands_and_each_target_exists():
    block = re.search(r"```bash\n(.*?)```", DOC, re.DOTALL).group(1)
    targets = [ln.split()[1] for ln in block.splitlines() if ln.startswith("make ")]
    assert targets == ["lint-ci", "precommit", "ci-exec"]
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    for target in targets:
        assert re.search(rf"^{target}:", makefile, re.MULTILINE), target


def test_fits_one_screen():
    assert len(DOC.splitlines()) <= 24
