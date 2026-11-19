"""Unit tests for reusable-main-ci-guard.yml's github-script body.

The script is extracted from the workflow and run under node against a stubbed
GitHub client, so no network is needed. Covers the default mode (latest
finished run) and the opt-in judge-head mode with its check-run fallback.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

WORKFLOW = (
    Path(__file__).resolve().parents[2] / ".github/workflows/reusable-main-ci-guard.yml"
)

RUNNER = """
const sc = JSON.parse(process.argv[3]);
const script = require("fs").readFileSync(process.argv[2], "utf8");
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const result = { failed: null };
const github = { rest: {
  repos: { getBranch: async () => ({ data: { commit: { sha: "HEAD1" } } }) },
  actions: { listWorkflowRuns: async () => ({ data: { workflow_runs: sc.runs || [] } }) },
  checks: { listForRef: async () => ({ data: { check_runs: sc.checks || [] } }) },
} };
const core = { info() {}, warning() {}, setFailed: (m) => { result.failed = String(m); } };
const context = { repo: { owner: "o", repo: "r" } };
process.env.WORKFLOW_ID = "ci.yml";
process.env.WORKFLOW_NAME = "CI";
process.env.JUDGE_HEAD = sc.judge ? "true" : "false";
process.env.FALLBACK_CHECK_NAME = sc.fallback || "";
new AsyncFunction("github", "context", "core", script)(github, context, core)
  .then(() => console.log(JSON.stringify(result)))
  .catch((e) => console.log(JSON.stringify({ failed: "THROWN: " + e.message })));
"""

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node not installed"
)


@pytest.fixture(scope="module")
def guard_js(tmp_path_factory):
    wf = yaml.safe_load(WORKFLOW.read_text())
    steps = wf["jobs"]["check-main-ci"]["steps"]
    script = next(
        s["with"]["script"]
        for s in steps
        if s.get("name", "").startswith("Check latest")
    )
    d = tmp_path_factory.mktemp("guard")
    (d / "guard.js").write_text(script)
    (d / "run.js").write_text(RUNNER)
    return d


def run(guard_js, scenario):
    out = subprocess.run(
        [
            "node",
            str(guard_js / "run.js"),
            str(guard_js / "guard.js"),
            json.dumps(scenario),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)["failed"]


def r(sha, conclusion):
    return {"head_sha": sha, "conclusion": conclusion, "html_url": "u"}


def c(status, conclusion):
    return {"status": status, "conclusion": conclusion, "html_url": "c"}


def test_default_latest_green_passes(guard_js):
    assert run(guard_js, {"runs": [r("OLD", "success")]}) is None


def test_default_skips_cancelled_runs(guard_js):
    assert run(guard_js, {"runs": [r("A", "cancelled"), r("B", "success")]}) is None


def test_default_latest_failure_fails(guard_js):
    assert run(guard_js, {"runs": [r("A", "failure")]}) is not None


def test_default_no_runs_fails(guard_js):
    assert run(guard_js, {"runs": []}) is not None


def test_head_green_run_passes(guard_js):
    assert run(guard_js, {"judge": True, "runs": [r("HEAD1", "success")]}) is None


def test_head_failed_run_fails(guard_js):
    assert run(guard_js, {"judge": True, "runs": [r("HEAD1", "failure")]}) is not None


def test_head_ignores_green_run_for_older_commit(guard_js):
    assert run(guard_js, {"judge": True, "runs": [r("OLD", "success")]}) is not None


def test_head_falls_back_to_green_check_run(guard_js):
    s = {
        "judge": True,
        "fallback": "CI Complete",
        "runs": [r("OLD", "success")],
        "checks": [c("completed", "success")],
    }
    assert run(guard_js, s) is None


def test_head_fallback_failed_check_fails(guard_js):
    s = {
        "judge": True,
        "fallback": "CI Complete",
        "runs": [],
        "checks": [c("completed", "failure")],
    }
    assert run(guard_js, s) is not None


def test_head_fallback_running_check_never_passes(guard_js):
    s = {
        "judge": True,
        "fallback": "CI Complete",
        "runs": [],
        "checks": [c("in_progress", None)],
    }
    assert run(guard_js, s) is not None


def test_head_without_fallback_name_fails_when_no_run(guard_js):
    assert (
        run(
            guard_js, {"judge": True, "runs": [], "checks": [c("completed", "success")]}
        )
        is not None
    )
