#!/usr/bin/env bash
# scripts/test-shift-left-parity.sh — check-shift-left-parity.sh fails when a
# configured hook can't run in CI and isn't listed in .shift-left.yml
# (shift-left spec R3, AC-SHIFT-03, -07).
set -euo pipefail

unset GIT_INDEX_FILE GIT_DIR GIT_WORK_TREE GIT_PREFIX GIT_COMMON_DIR
cd "$(dirname "$0")/../.."
HERE="$PWD"
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
parity() { # parity <repo> [args] -> $out, $rc
  local repo="$1"
  shift
  out="$(cd "$repo" && bash "$HERE/scripts/shift-left/check-shift-left-parity.sh" "$@" 2>&1)" && rc=0 || rc=$?
}
says() { grep -qE "$1" <<< "$out"; }

# A healthy repo: hooks at three stages, CI running all three, one local-only.
T="$TMP/template"
mkdir -p "$T/.github/workflows"
git -C "$T" init -q
cat > "$T/.pre-commit-config.yaml" << 'YML'
default_stages: [pre-commit]
repos:
  - repo: https://github.com/example/lint
    rev: v1
    hooks:
      - id: remote-lint
  - repo: local
    hooks:
      - id: lint
        name: lint
        entry: "true"
        language: system
      - id: tests
        name: tests
        entry: "true"
        language: system
        stages: [pre-commit, pre-push]
      - id: sast
        name: sast
        entry: "true"
        language: system
        stages: [pre-push]
      - id: msg
        name: msg
        entry: "true"
        language: system
        stages: [commit-msg]
      - id: stamp
        name: stamp
        entry: "true"
        language: system
YML
cat > "$T/.shift-left.yml" << 'YML'
local-only:
  - id: stamp
    reason: records that hooks ran in this clone
ci-only: []
YML
cat > "$T/.github/workflows/ci.yml" << 'YML'
jobs:
  hooks:
    steps:
      - run: pre-commit run --all-files --show-diff-on-failure
      - run: pre-commit run --all-files --show-diff-on-failure --hook-stage pre-push
      - run: pre-commit run --hook-stage commit-msg --commit-msg-filename "$f"
YML
scenario() {
  R="$TMP/$1"
  cp -R "$T" "$R"
}

echo "Healthy:"
scenario healthy
parity "$R"
check "exits 0" test "$rc" -eq 0
check "reports the hooks covered" says "6 hooks: 5 run in CI, 1 local-only"

echo "Skip lists for CI:"
parity "$R" --skip-list pre-commit
check "pre-commit: the local-only hooks" test "$out" = "stamp"
parity "$R" --skip-list pre-push
check "pre-push: local-only, plus hooks that already ran at pre-commit" test "$out" = "stamp,tests"

echo "Drift (AC-SHIFT-03, -07):"
scenario no-push-job
sed -i.bak '/--hook-stage pre-push/d' "$R/.github/workflows/ci.yml"
parity "$R"
check "CI stops running pre-push: fails" test "$rc" -eq 1
check "names the hook that no longer runs" says "FAIL.*sast.*pre-push"
check "a hook still run at another stage is fine" bash -c '! grep -q "FAIL.*tests" <<< "$0"' "$out"
scenario not-all-files
sed -i.bak 's/pre-commit run --all-files --show-diff-on-failure$/pre-commit run --show-diff-on-failure/' "$R/.github/workflows/ci.yml"
parity "$R"
check "pre-commit without --all-files doesn't count" says "FAIL.*lint"
scenario new-stage
cat >> "$R/.pre-commit-config.yaml" << 'YML'
      - id: on-checkout
        name: on checkout
        entry: "true"
        language: system
        stages: [post-checkout]
YML
parity "$R"
check "a hook at a stage CI never runs: fails" says "FAIL.*on-checkout.*post-checkout"
check "and says how to fix it" says "\.shift-left\.yml"

echo ".shift-left.yml itself:"
scenario no-reason
printf 'local-only:\n  - id: stamp\n' > "$R/.shift-left.yml"
parity "$R"
check "an entry without a reason fails" says "FAIL.*stamp.*reason"
scenario stale
printf 'local-only:\n  - id: stamp\n    reason: r\n  - id: gone\n    reason: r\n' > "$R/.shift-left.yml"
parity "$R"
check "an entry for a hook that doesn't exist fails" says "FAIL.*gone"
scenario no-file
rm "$R/.shift-left.yml"
parity "$R"
check "no .shift-left.yml: every hook runs in CI, none local-only" says "6 hooks: 6 run in CI, 0 local-only"
scenario ci-only
printf 'local-only:\n  - id: stamp\n    reason: r\nci-only:\n  - id: sast\n    reason: needs the compose stack\n' > "$R/.shift-left.yml"
parity "$R"
check "a ci-only hook must be at the manual stage" says "FAIL.*sast.*manual"

if [[ "$fails" -ne 0 ]]; then
  echo "test-shift-left-parity: $fails FAILED" >&2
  exit 1
fi
echo "test-shift-left-parity: all checks passed"
