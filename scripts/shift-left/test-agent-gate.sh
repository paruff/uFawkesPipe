#!/usr/bin/env bash
# scripts/shift-left/test-agent-gate.sh — the Stop-hook gate blocks an agent from
# finishing while a commit-stage hook fails on its uncommitted changes
# (shift-left spec R9, AC-SHIFT-10).
set -euo pipefail

# Keep a parent hook's environment out of the throwaway repos (see test-doctor.sh).
unset GIT_INDEX_FILE GIT_DIR GIT_WORK_TREE GIT_PREFIX GIT_COMMON_DIR SKIP
while read -r v; do unset "$v"; done < <(compgen -e | grep '^PRE_COMMIT')

cd "$(dirname "$0")/../.."
HERE="$PWD"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export PRE_COMMIT_HOME="$TMP/pre-commit-home"
fails=0
check() { # check <description> <command...>
  local desc="$1"
  shift
  if "$@"; then echo "  ok   $desc"; else
    echo "  FAIL $desc"
    fails=$((fails + 1))
  fi
}
# gate <repo> [stop_hook_active] -> $out (stdout+stderr), $rc
# The transcript lists the files the agent wrote (Write/Edit tool calls).
gate() {
  out="$(cd "$1" && printf '{"session_id":"t","stop_hook_active":%s,"transcript_path":"%s"}' "${2:-false}" "$TRANSCRIPT" | bash scripts/agent-gate.sh 2>&1)" && rc=0 || rc=$?
}
TRANSCRIPT="$TMP/transcript.jsonl"
: > "$TRANSCRIPT"
agent_wrote() { # agent_wrote <path> -> append a Write tool call to the transcript
  printf '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Write","input":{"file_path":"%s","content":"x"}}]}}\n' "$1" >> "$TRANSCRIPT"
}
says() { grep -qE "$1" <<< "$out"; }

# A repo whose hooks: `lint` fails on BAD; `fmt` rewrites UNFORMATTED and
# fails, as formatters do; `stamp` must not run (it would vouch for content
# that isn't committed).
R="$TMP/repo"
mkdir -p "$R/scripts" "$R/src"
cp scripts/shift-left/agent-gate.sh "$R/scripts/"
cat > "$R/scripts/lint.sh" << 'SH'
#!/usr/bin/env bash
! grep -l BAD "$@"
SH
cat > "$R/scripts/fmt.sh" << 'SH'
#!/usr/bin/env bash
rc=0
for f in "$@"; do grep -q UNFORMATTED "$f" && { sed -i.bak 's/UNFORMATTED/formatted/' "$f"; rm -f "$f.bak"; rc=1; }; done
exit $rc
SH
cat > "$R/scripts/stamp.sh" << 'SH'
#!/usr/bin/env bash
touch stamp-ran
SH
chmod +x "$R/scripts/"*.sh
cat > "$R/.pre-commit-config.yaml" << 'YML'
repos:
  - repo: local
    hooks:
      - id: lint
        name: lint
        entry: scripts/lint.sh
        language: script
        files: ^src/
      - id: fmt
        name: fmt
        entry: scripts/fmt.sh
        language: script
        files: ^src/
      - id: shift-left-stamp
        name: stamp
        entry: scripts/stamp.sh
        language: script
        always_run: true
        pass_filenames: false
YML
echo "ok" > "$R/src/app.txt"
printf 'stamp-ran\n' > "$R/.gitignore"
(cd "$R" && git init -q -b main && git add -A && git -c user.email=t@example.invalid -c user.name=t commit -qm "chore: init" --no-verify)

echo "Nothing to check:"
gate "$R"
check "a clean tree lets the agent stop" test "$rc" -eq 0
check "silently" test -z "$out"

echo "Changes that pass:"
echo "fine" > "$R/src/app.txt"
gate "$R"
check "a passing change lets the agent stop" test "$rc" -eq 0
check "the stamp hook is skipped" test ! -e "$R/stamp-ran"

echo "Changes that fail (AC-SHIFT-10):"
echo "BAD" > "$R/src/app.txt"
gate "$R"
check "a failing hook blocks the stop (exit 2)" test "$rc" -eq 2
check "and shows the agent which hook failed" says "lint"
check "and names the file" says "src/app.txt"
echo "BAD" > "$R/src/new.txt"
echo "BAD" > "$R/src/not-mine.txt"
agent_wrote "$R/src/new.txt"
gate "$R"
check "a new file the agent wrote is checked" says "src/new.txt"
check "an untracked file the agent didn't write is not" bash -c '! grep -q not-mine <<< "$0"' "$out"
rm "$R/src/new.txt"

echo "Loop guard:"
gate "$R" # blocks, and records this failure
gate "$R" true
check "blocked once already, same failure: stops blocking" test "$rc" -eq 0
check "and tells the person instead" says '"systemMessage":.*still failing'
echo "BAD" > "$R/src/other.txt"
agent_wrote "$R/src/other.txt"
gate "$R" true
check "blocked once already, but the failure changed: blocks" test "$rc" -eq 2
rm "$R/src/other.txt"

echo "Formatters fix their own:"
echo "UNFORMATTED" > "$R/src/app.txt"
gate "$R"
check "a formatter that fixed the file doesn't block" test "$rc" -eq 0
check "the fix is in the file" grep -qx formatted "$R/src/app.txt"

echo "Committed work:"
(cd "$R" && git add -A && git -c user.email=t@example.invalid -c user.name=t commit -qm "feat: x" --no-verify)
gate "$R"
check "nothing uncommitted: the commit hooks were the gate" test "$rc" -eq 0

cd "$HERE"
if [[ "$fails" -ne 0 ]]; then
  echo "test-agent-gate: $fails FAILED" >&2
  exit 1
fi
echo "test-agent-gate: all checks passed"
