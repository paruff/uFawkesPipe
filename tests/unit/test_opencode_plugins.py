"""Run the OpenCode plugin contract/behaviour tests through the unit suite.

The plugins under .opencode/plugins/ are JavaScript, so their tests use node's
built-in test runner (tests/plugins/*.test.mjs). This wrapper keeps a single
`make test-unit` entry point and fails the suite if any plugin stops exporting
the OpenCode V2 `{ id, setup }` contract or stops behaving as intended.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_opencode_plugins_contract_and_behaviour():
    """Every project plugin must load under OpenCode V2 and keep its behaviour."""
    if shutil.which("node") is None:
        pytest.skip("node is not installed")

    files = sorted((ROOT / "tests" / "plugins").glob("*.test.mjs"))
    assert files, "no plugin tests found under tests/plugins/"

    result = subprocess.run(
        ["node", "--test", *[str(f.relative_to(ROOT)) for f in files]],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
