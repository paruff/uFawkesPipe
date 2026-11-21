#!/usr/bin/env python3
"""Run shellcheck (as POSIX sh) over every step's `commands:` in Woodpecker files.

Steps run under /bin/sh, so a bashism passes on a laptop and fails only in the
agent (#297). Usage: woodpecker_shellcheck.py FILE [FILE...]. Exit 1 on findings.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

SEVERITY = "warning"


def step_scripts(doc: Any) -> list[tuple[str, str]]:
    """Return (step name, joined commands) for each step with a commands list."""
    if not isinstance(doc, dict):
        return []
    steps = doc.get("steps") or []
    if isinstance(doc.get("steps"), dict):
        steps = [{"name": k, **v} for k, v in doc["steps"].items()]
    out = []
    for step in steps:
        cmds = step.get("commands") if isinstance(step, dict) else None
        if cmds:
            out.append((str(step.get("name", "?")), "\n".join(str(c) for c in cmds)))
    return out


def check_file(path: Path) -> int:
    failed = 0
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"{path}: not valid YAML: {exc}")
        return 1
    for name, script in step_scripts(doc):
        with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as tmp:
            tmp.write("#!/bin/sh\n" + script + "\n")
        try:
            # Sourced paths only exist in the agent; SC1091 is info, below SEVERITY.
            res = subprocess.run(
                ["shellcheck", "-s", "sh", f"--severity={SEVERITY}", tmp.name],
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            Path(tmp.name).unlink()
        if res.returncode != 0:
            failed = 1
            print(f"{path}: step '{name}' fails shellcheck (sh):\n{res.stdout}")
    return failed


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: woodpecker_shellcheck.py FILE...", file=sys.stderr)
        return 2
    return max(check_file(Path(a)) for a in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
