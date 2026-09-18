"""Guard rails for scripts/bootstrap-secrets.sh (no existing test harness).

Regression: the script used to echo the first 20 chars of every generated
secret (AWS keys, GitHub App tokens, Azure client secret, base64 GCP SA key)
to stdout in its closing summary, which is a partial-disclosure risk if that
output lands in a CI log or shell history.
"""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "bootstrap-secrets.sh"


@pytest.mark.unit
def test_script_is_valid_bash():
    proc = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


@pytest.mark.unit
def test_closing_summary_does_not_echo_secret_values():
    source = SCRIPT.read_text()
    assert "SECRETS[$name]:0:" not in source, (
        "closing summary must not print any slice of a secret value — "
        "even a truncated prefix is a partial-disclosure risk in CI logs"
    )
