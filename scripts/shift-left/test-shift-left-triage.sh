#!/usr/bin/env bash
# scripts/test-shift-left-triage.sh — shift-left-triage.sh sorts a failed hook
# run into what an agent may fix and what goes to a person (shift-left spec
# R10, AC-SHIFT-11: seeded lint + format + failing test).
set -euo pipefail

cd "$(dirname "$0")/../.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0
check() { # check <description> <command...>
  local desc="$1"
  shift
  if "$@"; then echo "  ok   $desc"; else
    echo "  FAIL $desc"
    fails=$((fails + 1))
  fi
}

# AC-SHIFT-11's seeded run: a lint failure, a formatter that fixed files, a
# failing unit test, and hooks that passed or skipped.
cat > "$TMP/local.log" << 'LOG'
trim trailing whitespace.................................................Passed
Lint shell scripts with shellcheck.......................................Failed
- hook id: shellcheck
- exit code: 1

In scripts/x.sh line 3:
echo $1
     ^-- SC2086 (info): Double quote to prevent globbing and word splitting.

Format with Prettier (same version as CI)................................Failed
- hook id: prettier
- files were modified by this hook

docs/a.md 12ms
Unit tests (offline suites)..............................................Failed
- hook id: unit-tests
- exit code: 1

  FAIL     test-suite-status
Lint Go code.........................................(no files to check)Skipped
Some new hook............................................................Failed
- hook id: some-new-hook
- exit code: 1
LOG
want="$(printf 'fixed\tprettier\nmechanical\tshellcheck\njudgment\tunit-tests\njudgment\tsome-new-hook\n')"

echo "Local log:"
got="$(bash scripts/shift-left/shift-left-triage.sh < "$TMP/local.log")"
check "lint is mechanical, the formatter fixed itself, the test goes to a person" test "$got" = "$want"
check "reads a file argument too" test "$(bash scripts/shift-left/shift-left-triage.sh "$TMP/local.log")" = "$want"
check "an unknown hook is judgment, never assumed safe" grep -qx "judgment	some-new-hook" <<< "$got"

echo "CI log (gh run view --log-failed):"
sed 's/^/Pre-flight Checks\tRun pre-commit hooks\t2026-10-04T10:00:00.1234567Z /' "$TMP/local.log" > "$TMP/ci.log"
check "the same failures, through CI's prefixes" test "$(bash scripts/shift-left/shift-left-triage.sh < "$TMP/ci.log")" = "$want"

echo "Edge cases:"
printf 'lint....Passed\n' > "$TMP/clean.log"
check "no failures: no output" test -z "$(bash scripts/shift-left/shift-left-triage.sh < "$TMP/clean.log")"
printf 'Detect secrets with Gitleaks....Failed\n- hook id: gitleaks\n- files were modified by this hook\n' > "$TMP/odd.log"
check "files modified by a non-formatter is still judgment" test "$(bash scripts/shift-left/shift-left-triage.sh < "$TMP/odd.log")" = "$(printf 'judgment\tgitleaks')"

if [[ "$fails" -ne 0 ]]; then
  echo "test-shift-left-triage: $fails FAILED" >&2
  exit 1
fi
echo "test-shift-left-triage: all checks passed"
