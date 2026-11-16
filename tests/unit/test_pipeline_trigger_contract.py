"""The example request in docs/pipeline-trigger-contract.md must follow its own rules."""

import json
import re
from pathlib import Path

DOC = Path(__file__).parent.parent.parent / "docs" / "pipeline-trigger-contract.md"


def example():
    blocks = re.findall(
        r"```json\n(.*?)```", DOC.read_text(encoding="utf-8"), re.DOTALL
    )
    assert len(blocks) == 1, "the contract doc has exactly one JSON example"
    return json.loads(blocks[0])


def test_example_has_only_branch_and_variables():
    assert set(example()) == {"branch", "variables"}


def test_branch_is_a_non_empty_string():
    branch = example()["branch"]
    assert isinstance(branch, str) and branch


def test_variables_are_all_strings():
    variables = example()["variables"]
    assert variables
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in variables.items())


def test_doc_names_the_endpoint_and_bearer_auth():
    text = DOC.read_text(encoding="utf-8")
    assert "POST http://<woodpecker-host>:8000/api/repos/<repo-id>/pipelines" in text
    assert "Authorization: Bearer" in text
