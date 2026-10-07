#!/usr/bin/env bash
# scripts/shift-left/test-reinstall-hooks.sh — a clone whose hook config gains a
# stage gets that stage's git hook installed by its next checkout or merge,
# without a manual `pre-commit install` (shift-left plan G, uFawkesPipe#150).
# Found when a clone's pre-push hook was never installed because the config
# added the stage after `pre-commit install` had been run.
set -euo pipefail

# Hooks run by git export GIT_* and PRE_COMMIT_* variables; leaked into the
# throwaway repos they would point at the real one (see test-doctor.sh).
unset GIT_INDEX_FILE GIT_DIR GIT_WORK_TREE GIT_PREFIX GIT_COMMON_DIR
while read -r v; do unset "$v"; done < <(compgen -e | grep '^PRE_COMMIT')
unset SKIP

cd "$(dirname "$0")/../.."
HERE="$PWD"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export PRE_COMMIT_HOME="$TMP/pre-commit-home" # never touch the real cache
fails=0
check() { # check <description> <command...>
  local desc="$1"
  shift
  if "$@"; then echo "  ok   $desc"; else
    echo "  FAIL $desc"
    fails=$((fails + 1))
  fi
}
git_q() { git -c user.email=t@example.invalid -c user.name=t "$@"; }
hook_installed() { [[ -f "$R/.git/hooks/$1" ]]; }
hook_missing() { [[ ! -f "$R/.git/hooks/$1" ]]; }
says() { grep -qiE "$1" <<< "$out"; }
silent_about_installing() { ! grep -qi 'installed the' <<< "$out"; }

R="$TMP/clone"
mkdir -p "$R/scripts/shift-left"
cp scripts/shift-left/reinstall-hooks.sh "$R/scripts/shift-left/" 2> /dev/null || true
chmod +x "$R"/scripts/shift-left/*.sh 2> /dev/null || true

# The config as a repo has it today: the reinstall hook at post-checkout and post-merge.
config() { # config <extra default_install_hook_types...>
  local types="pre-commit, post-checkout, post-merge"
  [[ $# -gt 0 ]] && types="$types, $*"
  cat << YML
default_install_hook_types: [$types]
repos:
  - repo: local
    hooks:
      - id: shift-left-reinstall
        name: reinstall git hooks
        entry: scripts/shift-left/reinstall-hooks.sh
        language: script
        always_run: true
        pass_filenames: false
        verbose: true
        stages: [post-checkout, post-merge]
YML
}

(
  cd "$R"
  git init -q -b main
  git config maintenance.auto false
  git config gc.auto 0
  config > .pre-commit-config.yaml
  git add -A
  git_q commit -qm "chore: init"
  pre-commit install > /dev/null
  git_q checkout -qb adds-pre-push
  config pre-push > .pre-commit-config.yaml
  git_q commit -qam "chore: add the pre-push stage"
  git_q checkout -q main
  git_q checkout -qb adds-commit-msg
  config commit-msg > .pre-commit-config.yaml
  git_q commit -qam "chore: add the commit-msg stage"
  git_q checkout -q main
) > "$TMP/setup.log" 2>&1 || {
  cat "$TMP/setup.log"
  echo "test-reinstall-hooks: cannot build the throwaway repo" >&2
  exit 1
}

echo "Starting point (installed before the config gained a stage):"
check "pre-commit is installed" hook_installed pre-commit
check "and the two reinstall stages" hook_installed post-merge
check "pre-push is not" hook_missing pre-push

echo "A checkout of a branch whose config adds a stage:"
out="$(cd "$R" && git_q checkout adds-pre-push 2>&1)" || true
check "installs the stage's git hook" hook_installed pre-push
check "and says so" says "installed the pre-push"

echo "A checkout that adds nothing:"
out="$(cd "$R" && git_q checkout main 2>&1 && git_q checkout adds-pre-push 2>&1)" || true
check "says nothing about installing" silent_about_installing

echo "A merge that brings in a new stage:"
(cd "$R" && git_q checkout -q main)
check "commit-msg is not installed yet" hook_missing commit-msg
out="$(cd "$R" && git_q merge --ff-only adds-commit-msg 2>&1)" || true
check "installs it" hook_installed commit-msg

echo "It never fails a checkout:"
mkdir -p "$TMP/bare"
(cd "$TMP/bare" && git init -q)
out="$(cd "$TMP/bare" && bash "$HERE/scripts/shift-left/reinstall-hooks.sh" 2>&1)" && rc=0 || rc=$?
check "a repo with no pre-commit config: exit 0" test "$rc" -eq 0
check "and silent" test -z "$out"

if [[ "$fails" -ne 0 ]]; then
  echo "test-reinstall-hooks: $fails FAILED" >&2
  exit 1
fi
echo "test-reinstall-hooks: all checks passed"
