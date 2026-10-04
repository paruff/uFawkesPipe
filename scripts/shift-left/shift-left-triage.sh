#!/usr/bin/env bash
# scripts/shift-left-triage.sh — sort a failed hook run into what an agent may
# fix and what goes to a person (docs/ai-sdlc/shift-left/spec.md R10). Used by
# the shift-left-fix skill.
#
# Usage: shift-left-triage.sh [log]   (stdin by default)
#   The log is pre-commit output, local or from CI (`gh run view <id>
#   --log-failed`; its job, step and timestamp prefixes are ignored).
# Prints one "<class><TAB><hook id>" line per failed hook, in this order:
#   fixed       a formatter rewrote the files; rerun the hook to confirm
#   mechanical  a lint, format, schema or message rule; fix the code to
#               satisfy the rule, never the rule
#   judgment    a test, a security finding, a design rule, or a hook this
#               list doesn't know: hand it to a person with the log
set -euo pipefail

# The program goes in a variable: `python3 -` would read it from stdin, the log's.
PROG="$(
  cat << 'PY'
import re, sys

FORMATTERS = {"trailing-whitespace", "end-of-file-fixer", "mixed-line-ending", "prettier",
              "ruff-format", "shfmt", "terraform_fmt", "insert-license"}
MECHANICAL = FORMATTERS | {
    "ruff", "markdownlint", "yamllint", "shellcheck", "actionlint", "check-yaml", "check-json",
    "check-github-workflows", "check-dependabot", "conventional-commit", "conventional-commit-msg",
    "golangci-lint", "terraform_tflint", "terraform_docs",
}
# Everything else is judgment: unit-tests, semgrep, trivy, gitleaks, detect-private-key,
# check-merge-conflict, check-added-large-files, shift-left-parity, requirements-pin-check...

text = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
CI_PREFIX = re.compile(r"^(?:[^\t]*\t){2}\d{4}-\d\d-\d\dT[\d:.]+Z ?")
failed = []  # [hook id, files modified?]
current = None
for raw in text.splitlines():
    line = CI_PREFIX.sub("", raw)
    if re.search(r"\.{3,}.*(Passed|Failed|Skipped)$", line):
        current = None
    m = re.match(r"- hook id: (\S+)", line)
    if m:
        current = [m.group(1), False]
        failed.append(current)
    elif current and line.startswith("- files were modified by this hook"):
        current[1] = True

ORDER = {"fixed": 0, "mechanical": 1, "judgment": 2}
rows = []
for i, (hook, modified) in enumerate(failed):
    if hook in FORMATTERS and modified:
        cls = "fixed"
    elif hook in MECHANICAL:
        cls = "mechanical"
    else:
        cls = "judgment"
    rows.append((ORDER[cls], i, cls, hook))
for _, _, cls, hook in sorted(rows):
    print(f"{cls}\t{hook}")
PY
)"
exec python3 -c "$PROG" "$@"
