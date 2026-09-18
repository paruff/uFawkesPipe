"""Regression check for scripts/dora-log.sh's duration_ms/status fields.

P3-5 (Alloy log parsing) needs stage/status/duration_ms in the JSON pipeline
logs to extract as Loki labels — dora_start/dora_end previously emitted
neither status nor duration_ms at all.
"""

import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "dora-log.sh"


@pytest.mark.unit
def test_script_is_valid_bash():
    proc = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


@pytest.mark.unit
def test_dora_end_emits_status_and_duration_ms():
    script = f'''
set -e
source "{SCRIPT}"
export CI_PIPELINE_NUMBER=42 CI_REPO="org/app" CI_STEP_NAME="test-step"
dora_start "test-step"
sleep 0.2
dora_end "test-step"
dora_end "other-step" "failure"
'''
    proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    lines = [json.loads(line) for line in proc.stdout.strip().splitlines()]
    assert len(lines) == 3

    start, end_ok, end_fail = lines
    assert "duration_ms" not in start, "dora_start must not claim a duration"

    assert end_ok["status"] == "success"
    assert 150 <= end_ok["duration_ms"] <= 5000, (
        f"expected ~200ms for a 0.2s sleep, got {end_ok['duration_ms']}"
    )

    assert end_fail["status"] == "failure"
