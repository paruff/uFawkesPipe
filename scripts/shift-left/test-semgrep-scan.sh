#!/usr/bin/env bash
# scripts/shift-left/test-semgrep-scan.sh — semgrep-scan.sh uses the registry ruleset when
# online, the last fetched copy when not, and never passes without rules
# (shift-left spec R2, AC-SHIFT-05; decision 1).
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
run() { out="$(bash scripts/shift-left/semgrep-scan.sh "$@" 2>&1)" && rc=0 || rc=$?; }

# Stubs: curl "fetches" the ruleset unless OFFLINE is set; semgrep records its
# arguments and fails when the scanned file contains BAD.
mkdir -p "$TMP/bin"
cat > "$TMP/bin/curl" << 'STUB'
#!/usr/bin/env bash
[[ -n "${OFFLINE:-}" ]] && exit 6
for ((i = 1; i <= $#; i++)); do [[ "${!i}" == -o ]] && { j=$((i + 1)); echo "rules: [] # fresh" > "${!j}"; }; done
exit 0
STUB
cat > "$TMP/bin/semgrep" << STUB
#!/usr/bin/env bash
echo "\$*" > "$TMP/semgrep-args"
for a in "\$@"; do [[ -f "\$a" ]] && grep -q BAD "\$a" && { echo "finding in \$a"; exit 1; }; done
exit 0
STUB
chmod +x "$TMP/bin/"*
export PATH="$TMP/bin:$PATH"
export SEMGREP_RULES_CACHE="$TMP/cache/p-ci.yml"
unset SHIFT_LEFT_ALLOW_MISSING OFFLINE
echo "clean" > "$TMP/ok.py"
echo "BAD" > "$TMP/bad.py"

echo "Online:"
run "$TMP/ok.py"
check "passes a clean file" test "$rc" -eq 0
check "scans with the freshly fetched ruleset" grep -q -- "--config $SEMGREP_RULES_CACHE" "$TMP/semgrep-args"
check "caches it for offline use" grep -q fresh "$SEMGREP_RULES_CACHE"
check "fails on errors (--error)" grep -q -- "--error" "$TMP/semgrep-args"
run "$TMP/bad.py"
check "a finding fails the hook" test "$rc" -eq 1
check "and shows the finding" grep -q "finding in" <<< "$out"

echo "Offline:"
OFFLINE=1 run "$TMP/ok.py"
check "with a cached ruleset: passes" test "$rc" -eq 0
check "says it used the cached copy" grep -q "offline.*cached" <<< "$out"
rm -f "$SEMGREP_RULES_CACHE"
OFFLINE=1 run "$TMP/ok.py"
check "no cache: fails rather than scanning with nothing" test "$rc" -eq 1
OFFLINE=1 SHIFT_LEFT_ALLOW_MISSING=semgrep-rules run "$TMP/ok.py"
check "allowed: loud SKIPPED and passes" bash -c '[[ $0 -eq 0 ]] && grep -qx "SKIPPED (tool missing): semgrep-rules" <<< "$1"' "$rc" "$out"

if [[ "$fails" -ne 0 ]]; then
  echo "test-semgrep-scan: $fails FAILED" >&2
  exit 1
fi
echo "test-semgrep-scan: all checks passed"
