import json
import re
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
EXACT = re.compile(r"^@ni-c/woodpecker-ci-mcp@\d+\.\d+\.\d+$")


def _claude() -> dict:
    return json.loads((REPO / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]


def _opencode() -> dict:
    return json.loads(
        (REPO / ".opencode" / "opencode.json").read_text(encoding="utf-8")
    )["mcp"]


def test_woodpecker_mcp_is_pinned_read_only_essential():
    entry = _claude()["woodpecker"]
    assert any(EXACT.match(a) for a in entry["args"]), entry["args"]
    assert entry["env"]["WOODPECKER_READ_ONLY"] == "true"
    assert entry["env"]["WOODPECKER_ALLOW_TOOLS"] == "essential"


def test_woodpecker_token_comes_from_env_not_the_file():
    for token in (
        _claude()["woodpecker"]["env"]["WOODPECKER_TOKEN"],
        _opencode()["woodpecker"]["environment"]["WOODPECKER_TOKEN"],
    ):
        assert "MCP_TOKEN" in token and token.startswith(("${", "{env:"))


def test_opencode_entry_matches_claude_entry():
    entry = _opencode()["woodpecker"]
    assert any(EXACT.match(a) for a in entry["command"])
    assert entry["environment"]["WOODPECKER_READ_ONLY"] == "true"
    assert entry["environment"]["WOODPECKER_ALLOW_TOOLS"] == "essential"


def test_no_write_entry_committed():
    assert "woodpecker-write" not in _claude()
    assert "woodpecker-write" not in _opencode()
