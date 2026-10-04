#!/usr/bin/env bash
# scripts/require-tool.sh — a hook never passes silently on a missing tool
# (docs/ai-sdlc/shift-left/spec.md R4, AC-SHIFT-02).
#
# Usage: require-tool.sh <tool> [--min <version>] [-- <command...>]
#   Tool on PATH (and at least --min): runs the command, exits with its code.
#   Tool missing or too old: exits 1 with an install hint.
#   SHIFT_LEFT_ALLOW_MISSING=<tool>[,<tool>...] turns a missing tool into a
#   loud "SKIPPED (tool missing): <tool>" and exit 0. A too-old tool is never
#   skipped: it gives wrong answers, not none.
#
# Used as a hook entry in place of `language: system` with a bare tool name:
#   entry: scripts/require-tool.sh helm -- bash -c 'helm lint ...'
#   language: script
set -euo pipefail

tool="${1:?usage: require-tool.sh <tool> [--min <version>] [-- <command...>]}"
shift
min=""
if [[ "${1:-}" == "--min" ]]; then
  min="${2:?--min needs a version}"
  shift 2
fi
[[ "${1:-}" == "--" ]] && shift

if ! command -v "$tool" > /dev/null; then
  if [[ ",${SHIFT_LEFT_ALLOW_MISSING:-}," == *",$tool,"* ]]; then
    echo "SKIPPED (tool missing): $tool"
    exit 0
  fi
  echo "require-tool: $tool is not installed, so this check cannot run." >&2
  echo "  Install it (the devcontainer has it), or to skip it knowingly:" >&2
  echo "  SHIFT_LEFT_ALLOW_MISSING=$tool git commit ..." >&2
  exit 1
fi

if [[ -n "$min" ]]; then
  # Tools disagree on the flag; take the first version-looking string any of them prints.
  found="$({ "$tool" --version || "$tool" version || "$tool" -v; } 2> /dev/null | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1 || true)"
  if [[ -z "$found" || "$(printf '%s\n%s\n' "$min" "$found" | sort -V | head -1)" != "$min" ]]; then
    echo "require-tool: $tool ${found:-(version unknown)} is older than the minimum $min." >&2
    exit 1
  fi
fi

[[ $# -eq 0 ]] && exit 0
exec "$@"
