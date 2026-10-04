#!/usr/bin/env bash
# scripts/shift-left/semgrep-scan.sh — SAST at pre-push with the registry's p/ci ruleset
# (uFawkes.dev shift-left spec R2, AC-SHIFT-05; decision 1: online if available, offline
# if not).
#
# Online, it fetches p/ci and scans with that file, so a laptop and CI use the
# same rules. It keeps the copy (outside git: registry rules are licensed
# against redistribution) and uses it when the registry can't be reached. With
# no copy at all it fails, unless SHIFT_LEFT_ALLOW_MISSING names semgrep-rules.
#
# Usage: semgrep-scan.sh <files...>   (the pre-commit hook passes them)
# SEMGREP_RULES_CACHE overrides where the copy lives (tests).
set -euo pipefail

cache="${SEMGREP_RULES_CACHE:-$(git rev-parse --git-path shift-left)/semgrep-p-ci.yml}"
mkdir -p "$(dirname "$cache")"

new="$(mktemp "$cache.XXXXXX")"
if curl -fsSL --max-time 15 -o "$new" https://semgrep.dev/c/p/ci 2> /dev/null; then
  mv "$new" "$cache"
else
  rm -f "$new"
  if [[ ! -s "$cache" ]]; then
    if [[ ",${SHIFT_LEFT_ALLOW_MISSING:-}," == *",semgrep-rules,"* ]]; then
      echo "SKIPPED (tool missing): semgrep-rules"
      exit 0
    fi
    echo "semgrep-scan: the registry is unreachable and no ruleset has been fetched yet." >&2
    echo "  Push once while online, or skip knowingly: SHIFT_LEFT_ALLOW_MISSING=semgrep-rules git push" >&2
    exit 1
  fi
  echo "semgrep-scan: offline, using the cached p/ci from $(date -r "$cache" +%Y-%m-%d)"
fi

exec semgrep scan --config "$cache" --error --metrics=off --disable-version-check --quiet "$@"
