#!/usr/bin/env bash
# scripts/shift-left/agent-gate.sh — an agent can't finish while a commit-stage hook fails
# on its changes (uFawkes.dev docs/ai-sdlc/shift-left/spec.md R9). Run as a
# Claude Code Stop hook through the repo's shim (`bash scripts/shift-left.sh
# agent-gate` in .claude/settings.json); reads the hook's JSON on stdin.
#
# Runs the pre-commit stage's hooks on the uncommitted changes: every tracked
# file that differs from HEAD, and the untracked files the agent itself wrote
# (Write/Edit calls in the transcript). Untracked files it didn't write, like a
# local scratch directory, are not its work and would only cry wolf. The gate a
# commit would apply, applied before the agent says it's done; committed work
# already went through it.
#   pass             exit 0, silent
#   formatters fixed exit 0: a second run separates a fix from a real failure
#   fail             exit 2: Claude Code blocks the stop and shows the agent this
# Loop guard: if the agent was already blocked once (stop_hook_active) and the
# failure is unchanged, it lets the agent stop and tells the person instead.
#
# The stamp hooks are skipped: a stamp would vouch for content not yet committed.
set -uo pipefail

input="$(cat)"
field() { python3 -c 'import json, sys; v = json.load(sys.stdin).get(sys.argv[1]); print(str(v).lower() if isinstance(v, bool) else (v or ""))' "$1" <<< "$input" 2> /dev/null; }
active="$(field stop_hook_active)"
transcript="$(field transcript_path)"
cd "$(git rev-parse --show-toplevel 2> /dev/null)" || exit 0
# Not set up here: the doctor reports that at session start.
command -v pre-commit > /dev/null && [[ -f .pre-commit-config.yaml ]] || exit 0

# The paths the agent wrote, relative to the repo root.
written() {
  [[ -f "$transcript" ]] || return 0
  python3 - "$transcript" "$PWD" << 'PY2'
import json, os, sys
root = os.path.realpath(sys.argv[2])
for line in open(sys.argv[1], errors="replace"):
    try:
        content = json.loads(line).get("message", {}).get("content", [])
    except (ValueError, AttributeError):
        continue
    for c in content if isinstance(content, list) else []:
        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            p = (c.get("input") or {}).get("file_path") or (c.get("input") or {}).get("notebook_path")
            if p:
                rel = os.path.relpath(os.path.realpath(p), root)
                if not rel.startswith(".."):
                    print(rel)
PY2
}
mapfile -t files < <({
  git diff --name-only --diff-filter=d HEAD 2> /dev/null
  comm -12 <(git ls-files --others --exclude-standard | sort -u) <(written | sort -u)
} | sort -u)
[[ ${#files[@]} -eq 0 ]] && exit 0

run() { SKIP="shift-left-stamp,shift-left-stamp-pre-push${SKIP:+,$SKIP}" pre-commit run --files "${files[@]}" 2>&1; }
out="$(run)" && exit 0
out="$(run)" && exit 0

state="$(git rev-parse --git-path shift-left)"
mkdir -p "$state"
sig="$(printf '%s' "$out" | shasum | awk '{print $1}')"
if [[ "$active" == true && "$(cat "$state/agent-gate-last" 2> /dev/null)" == "$sig" ]]; then
  msg="agent gate: commit-stage hooks are still failing on uncommitted changes after the agent's retry, so it stopped instead of looping. See: pre-commit run --files $(printf '%s ' "${files[@]}")"
  python3 -c 'import json, sys; print(json.dumps({"systemMessage": sys.argv[1]}))' "$msg"
  exit 0
fi
echo "$sig" > "$state/agent-gate-last"
{
  echo "agent gate: commit-stage hooks fail on your uncommitted changes. Fix them before finishing;"
  echo "never with --no-verify, and never by weakening a hook or a test. The shift-left-fix skill"
  echo "(bash scripts/shift-left.sh shift-left-triage) says which failures are yours to fix and which go to a person."
  echo
  tail -60 <<< "$out"
} >&2
exit 2
