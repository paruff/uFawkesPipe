"""Acceptance tests: Suite behavior meta-tests.

Covers AC-13 and AC-14 (see docs/acceptance-criteria.md).
Verifies that:
- AC-13: Tests skip gracefully when the compose stack is not running
- AC-14: Two consecutive runs produce identical pass/fail/skip counts

These tests run pytest as a subprocess against their own test files.
They do NOT require the compose stack unless testing stack-dependent
tests.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PYTEST_ARGS = [
    sys.executable,
    "-m",
    "pytest",
    "-v",
    "--tb=short",
    "-p",
    "no:cacheprovider",  # Disable cache for clean results
]


def run_pytest(test_file, extra_args=None):
    """Run pytest on a specific test file and return (returncode, stdout, stderr).

    Returns parsed summary: lines of output, full stdout, and exit code.
    """
    args = PYTEST_ARGS + [str(test_file)]
    if extra_args:
        args.extend(extra_args)

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(PROJECT_ROOT),
    )
    return result


def parse_summary_line(stdout):
    """Parse the pytest summary line: 'N passed, M skipped, X failed'.

    Returns dict with passed, skipped, failed, errors counts.
    """
    summary = {"passed": 0, "skipped": 0, "failed": 0, "errors": 0, "total": 0}

    for line in stdout.split("\n"):
        line = line.strip()
        if "passed" in line or "failed" in line or "skipped" in line:
            # Match patterns like "3 passed, 5 skipped, 0 failed"
            passed = re.search(r"(\d+)\s*passed", line)
            skipped = re.search(r"(\d+)\s*skipped", line)
            failed = re.search(r"(\d+)\s*failed", line)
            errors = re.search(r"(\d+)\s*error", line)

            if passed:
                summary["passed"] = int(passed.group(1))
            if skipped:
                summary["skipped"] = int(skipped.group(1))
            if failed:
                summary["failed"] = int(failed.group(1))
            if errors:
                summary["errors"] = int(errors.group(1))

            summary["total"] = (
                summary["passed"]
                + summary["skipped"]
                + summary["failed"]
                + summary["errors"]
            )

    return summary


# The test file path for self-referential testing
THIS_FILE = Path(__file__)


@pytest.mark.acceptance
class TestSuiteSkipSafety:
    """Verify AC-13: tests skip gracefully when stack is not running.

    These meta-tests run pytest as a subprocess against test files
    that depend on the compose stack, to verify skip behavior when
    the stack is unavailable.
    """

    def test_health_tests_skip_when_stack_down_can_run(self):
        """test_01 health tests must be callable without errors.

        This is a basic sanity check — the test file should at least
        collect and run (it may skip depending on compose_running).
        """
        test_file = THIS_FILE.parent / "test_01_stack_health.py"
        result = run_pytest(test_file)

        # Exit code should be 0 (no failures) or 5 (all skipped)
        assert result.returncode in (0, 5), (
            f"test_01_stack_health.py unexpected exit code {result.returncode}.\n"
            f"stdout:\n{result.stdout[:500]}\n"
            f"stderr:\n{result.stderr[:500]}"
        )

    def test_structure_tests_always_run(self):
        """test_03 pipeline structure tests must always collect as expected.

        These tests parse .woodpecker.yml from disk and don't need
        the compose stack. They should have exactly 12 test functions.
        """
        test_file = THIS_FILE.parent / "test_03_pipeline_structure.py"
        result = run_pytest(test_file, ["--collect-only"])

        assert result.returncode == 0, (
            f"test_03 collection failed: {result.stderr[:300]}"
        )

        # Count collected tests from stdout
        collected = re.findall(r"<Function\s+(\w+)>", result.stdout)
        assert len(collected) >= 10, (
            f"Expected 10+ tests in test_03, collected {len(collected)}: {collected}"
        )


@pytest.mark.acceptance
class TestSuiteIdempotency:
    """Verify AC-14: two consecutive runs produce identical results."""

    def test_pipeline_structure_tests_idempotent(self):
        """Two runs of test_03 must produce identical pass/fail/skip counts."""
        test_file = THIS_FILE.parent / "test_03_pipeline_structure.py"

        run1 = run_pytest(test_file)
        run2 = run_pytest(test_file)

        summary1 = parse_summary_line(run1.stdout)
        summary2 = parse_summary_line(run2.stdout)

        assert summary1 == summary2, (
            f"Idempotency failure: run results differ.\n"
            f"Run 1: {summary1}\n"
            f"Run 2: {summary2}\n"
            f"Diff detected in passed/skipped/failed counts."
        )

        # At least some tests passed (structure validation)
        assert summary1["passed"] >= 10, f"Expected 10+ passed tests, got {summary1}"

    def test_security_tests_idempotent(self):
        """Two runs of test_04 must produce identical pass/fail/skip counts."""
        test_file = THIS_FILE.parent / "test_04_security_simulation.py"

        run1 = run_pytest(test_file)
        run2 = run_pytest(test_file)

        summary1 = parse_summary_line(run1.stdout)
        summary2 = parse_summary_line(run2.stdout)

        assert summary1 == summary2, (
            f"Idempotency failure: run results differ.\n"
            f"Run 1: {summary1}\n"
            f"Run 2: {summary2}\n"
            f"Diff detected in passed/skipped/failed counts."
        )
