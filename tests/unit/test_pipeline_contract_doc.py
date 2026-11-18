"""docs/pipeline-contract.md must describe what scripts/generate_woodpecker_yml.py does (#221)."""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_woodpecker_yml as gen  # noqa: E402

DOC = (ROOT / "docs" / "pipeline-contract.md").read_text()
# Fields the generator never reads, so the doc must not list them.
IGNORED_FIELDS = ("retry", "parallel", "artifacts.paths", "workspace.cleanup")


def _section(heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}.*?(?=^## )", DOC, re.S | re.M)
    assert match, f"no '## {heading}' section"
    return match.group(0)


def _required_rows(section: str) -> list[str]:
    """Field names whose 'Required' cell is `yes` in the section's first table."""
    table = section.split("\n\n")[1:]
    rows = [r for block in table for r in block.splitlines() if r.startswith("|")]
    names = []
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) > 2 and cells[2] == "yes":
            names.append(cells[0].strip("`"))
    return names


def _contract(tmp_path: Path, app: dict) -> Path:
    path = tmp_path / ".fawkespipe.yml"
    import yaml

    path.write_text(yaml.safe_dump({"app": app, "build": {"builder": "cnb"}}))
    return path


@pytest.mark.unit
@pytest.mark.parametrize("field", _required_rows(_section("app — Application Metadata")))
def test_every_app_field_the_doc_requires_is_enforced(tmp_path, field):
    app = {"name": "x", "type": "service", "language": "python"}
    del app[field]
    with pytest.raises(gen.ContractError, match=field):
        gen.load_contract(_contract(tmp_path, app))


@pytest.mark.unit
def test_doc_requires_only_what_the_generator_enforces():
    assert _required_rows(_section("app — Application Metadata")) == ["language"]
    build_required = _required_rows(_section("build — Build Configuration"))
    assert build_required == [], f"generator enforces no build.* field, doc requires {build_required}"


@pytest.mark.unit
@pytest.mark.parametrize("field", IGNORED_FIELDS)
def test_doc_does_not_list_fields_the_generator_ignores(field):
    assert field not in _section("advanced — Advanced Configuration")
