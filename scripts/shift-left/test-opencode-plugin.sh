#!/usr/bin/env bash
# scripts/shift-left/test-opencode-plugin.sh — runs test-opencode-plugin.mjs
# with Node's built-in test runner. Node is a prerequisite, not a dependency
# added to the repo: no package.json, nothing installed.
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v node > /dev/null; then
  echo "test-opencode-plugin: node is required (the plugin runs inside OpenCode)" >&2
  exit 1
fi
node --test test-opencode-plugin.mjs
echo "test-opencode-plugin: all checks passed"
