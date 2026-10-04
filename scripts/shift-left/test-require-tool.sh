#!/usr/bin/env bash
# scripts/test-require-tool.sh — require-tool.sh never lets a hook pass
# silently on a missing or too-old tool (shift-left spec R4, AC-SHIFT-02).
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
# run <args...> -> sets $out and $rc
run() { out="$(bash scripts/shift-left/require-tool.sh "$@" 2>&1)" && rc=0 || rc=$?; }

mkdir -p "$TMP/bin"
printf '#!/usr/bin/env bash\necho "fakelint version 1.4.2"\n' > "$TMP/bin/fakelint"
chmod +x "$TMP/bin/fakelint"
export PATH="$TMP/bin:$PATH"
unset SHIFT_LEFT_ALLOW_MISSING

echo "Missing tool:"
run nosuchtool -- true
check "fails" test "$rc" -eq 1
check "says how to allow it, ready to paste" grep -q "SHIFT_LEFT_ALLOW_MISSING=nosuchtool git commit" <<< "$out"
SHIFT_LEFT_ALLOW_MISSING="other,nosuchtool" run nosuchtool -- false
check "allowed: passes without running the command" test "$rc" -eq 0
check "allowed: prints a loud SKIPPED line" grep -qx "SKIPPED (tool missing): nosuchtool" <<< "$out"
SHIFT_LEFT_ALLOW_MISSING="nosuchtoolx" run nosuchtool -- true
check "allow list matches whole names only" test "$rc" -eq 1

echo "Present tool:"
run fakelint -- bash -c 'echo ran; exit 0'
check "runs the command" grep -qx "ran" <<< "$out"
run fakelint -- bash -c 'exit 3'
check "passes the command's failure through" test "$rc" -eq 3
run fakelint
check "no command: just checks" test "$rc" -eq 0

echo "Minimum version:"
run fakelint --min 1.4.0 -- true
check "equal or newer passes" test "$rc" -eq 0
run fakelint --min 1.10.0 -- true
check "older fails (1.4.2 < 1.10.0, compared as versions)" test "$rc" -eq 1
check "says found and wanted" grep -q "1.4.2.*1.10.0" <<< "$out"

if [[ "$fails" -ne 0 ]]; then
  echo "test-require-tool: $fails FAILED" >&2
  exit 1
fi
echo "test-require-tool: all checks passed"
