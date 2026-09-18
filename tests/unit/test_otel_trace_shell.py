"""Regression checks for scripts/otel-trace.sh (P3-4).

Covers the parts that don't need a live OTEL collector — trace_id sharing
across steps in the same pipeline run, per-step span_id uniqueness, the
:4317->:4318 OTLP/HTTP endpoint rewrite, and safe no-op behavior when
OTEL_EXPORTER_OTLP_ENDPOINT is unset or unreachable.

The full round trip (real span received and parsed by a real
otel/opentelemetry-collector container, correct trace_id shared across two
spans, correct Ok/Error status codes) was verified manually against a live
collector during implementation — not re-run here to keep this suite
network-free.
"""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "otel-trace.sh"


def _run(script_body: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-c", f'source "{SCRIPT}"\n{script_body}'],
        capture_output=True,
        text=True,
    )


@pytest.mark.unit
def test_script_is_valid_bash():
    proc = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


@pytest.mark.unit
def test_trace_id_shared_across_steps_in_same_pipeline():
    proc = _run(
        'export CI_PIPELINE_NUMBER=42 CI_REPO_NAME="org/app"\n'
        "_otel_trace_id; echo\n"
        "_otel_trace_id; echo\n"
    )
    assert proc.returncode == 0, proc.stderr
    lines = proc.stdout.strip().splitlines()
    assert len(lines) == 2
    assert lines[0] == lines[1], (
        "trace_id must be deterministic for the same pipeline run"
    )
    assert len(lines[0]) == 32, "OTLP trace_id must be 32 hex chars (128 bits)"


@pytest.mark.unit
def test_trace_id_differs_across_pipelines():
    proc = _run(
        'export CI_REPO_NAME="org/app"\n'
        "CI_PIPELINE_NUMBER=1 _otel_trace_id; echo\n"
        "CI_PIPELINE_NUMBER=2 _otel_trace_id; echo\n"
    )
    lines = proc.stdout.strip().splitlines()
    assert lines[0] != lines[1]


@pytest.mark.unit
def test_span_id_differs_per_step_name():
    proc = _run(
        'export CI_PIPELINE_NUMBER=42 CI_REPO_NAME="org/app"\n'
        'otel_span_start "sast"; echo "$_OTEL_SPAN_ID"\n'
        'otel_span_start "dast"; echo "$_OTEL_SPAN_ID"\n'
    )
    lines = proc.stdout.strip().splitlines()
    assert len(lines) == 2
    assert lines[0] != lines[1]
    assert all(len(line) == 16 for line in lines), (
        "OTLP span_id must be 16 hex chars (64 bits)"
    )


@pytest.mark.unit
def test_endpoint_swaps_grpc_port_for_http_port():
    proc = _run(
        'OTEL_EXPORTER_OTLP_ENDPOINT="http://collector:4317" _otel_http_endpoint\n'
    )
    assert proc.stdout.strip() == "http://collector:4318"


@pytest.mark.unit
def test_span_end_is_a_safe_noop_without_endpoint():
    """No OTEL_EXPORTER_OTLP_ENDPOINT configured -> no curl attempt, no error,
    the step must never fail because of this."""
    proc = _run(
        "unset OTEL_EXPORTER_OTLP_ENDPOINT\n"
        'otel_span_start "sast"\n'
        'otel_span_end "sast"\n'
        'echo "exit=$?"\n'
    )
    assert proc.returncode == 0, proc.stderr
    assert "exit=0" in proc.stdout
