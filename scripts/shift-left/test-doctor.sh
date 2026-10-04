#!/usr/bin/env bash
# scripts/shift-left/test-doctor.sh — fault injection for scripts/doctor.sh (shift-left
# spec R5, AC-SHIFT-01, -02, -07). Each scenario copies one healthy throwaway
# repo, breaks one thing, and asserts the doctor names it, and only it.
set -euo pipefail

# Git exports GIT_INDEX_FILE (and friends) to hooks; run from the unit-tests
# hook, they would point the throwaway repos at the real index. See
# test-artifact-chain.sh.
unset GIT_INDEX_FILE GIT_DIR GIT_WORK_TREE GIT_PREFIX GIT_COMMON_DIR
# Likewise a real push exports PRE_COMMIT_TO_REF (and friends) to its hooks;
# leaked into a throwaway push, the stamp records the outer repo's ref.
while read -r v; do unset "$v"; done < <(compgen -e | grep '^PRE_COMMIT')
# And CI's SKIP list (shift-left-stamp, ...) would skip the throwaway repos' stamps.
unset SKIP

cd "$(dirname "$0")/../.."
HERE="$PWD"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export PRE_COMMIT_HOME="$TMP/pre-commit-home" # never touch the real cache
unset SHIFT_LEFT_ALLOW_MISSING
fails=0
check() { # check <description> <command...>
  local desc="$1"
  shift
  if "$@"; then echo "  ok   $desc"; else
    echo "  FAIL $desc"
    fails=$((fails + 1))
  fi
}
# doctor <repo> [args] -> sets $out and $rc
doctor() {
  local repo="$1"
  shift
  out="$(cd "$repo" && bash scripts/shift-left/doctor.sh "$@" 2>&1)" && rc=0 || rc=$?
}
says() { grep -qE "$1" <<< "$out"; }
fails_only() { # the FAIL lines name exactly this check id
  [[ "$(grep -oE 'FAIL +D[0-9]' <<< "$out" | awk '{print $2}' | sort -u | tr '\n' ' ')" == "$1 " ]]
}
git_q() { git -c user.email=t@example.invalid -c user.name=t "$@"; }

# --- the healthy template ----------------------------------------------------
T="$TMP/template"
mkdir -p "$T/scripts/shift-left" "$T/src"
cp scripts/shift-left/{doctor,require-tool,shift-left-stamp,check-shift-left-parity}.sh "$T/scripts/shift-left/"
cat > "$T/scripts/lint.sh" << 'SH'
#!/usr/bin/env bash
exit 0
SH
cat > "$T/scripts/push-gate.sh" << 'SH'
#!/usr/bin/env bash
[[ ! -e .fail-push ]]
SH
chmod +x "$T/scripts/"*.sh "$T/scripts/shift-left/"*.sh
echo "x = 1" > "$T/src/app.py"
cat > "$T/.pre-commit-config.yaml" << 'YML'
minimum_pre_commit_version: "3.0.0"
default_install_hook_types: [pre-commit, commit-msg, pre-push]
repos:
  - repo: local
    hooks:
      - id: lint
        name: lint
        entry: scripts/lint.sh
        language: script
        files: ^src/
      - id: needs-tool
        name: needs a tool
        entry: scripts/shift-left/require-tool.sh git -- true
        language: script
        files: ^src/
      - id: never-applies
        name: tool missing, but no file here uses it
        entry: scripts/shift-left/require-tool.sh nosuchtool -- true
        language: script
        files: ^infra/
      - id: push-gate
        name: a pre-push hook that fails while .fail-push exists
        entry: scripts/push-gate.sh
        language: script
        pass_filenames: false
        always_run: true
        stages: [pre-push]
      - id: commit-msg
        name: commit msg
        entry: "true"
        language: system
        stages: [commit-msg]
      - id: shift-left-stamp
        name: stamp
        entry: scripts/shift-left/shift-left-stamp.sh pre-commit
        language: script
        always_run: true
        pass_filenames: false
      - id: shift-left-stamp-pre-push
        name: stamp
        entry: scripts/shift-left/shift-left-stamp.sh pre-push
        language: script
        always_run: true
        pass_filenames: false
        stages: [pre-push]
YML
mkdir -p "$T/.github/workflows"
cat > "$T/.github/workflows/ci.yml" << 'YML'
jobs:
  hooks:
    steps:
      - run: pre-commit run --all-files
      - run: pre-commit run --all-files --hook-stage pre-push
      - run: pre-commit run --hook-stage commit-msg --commit-msg-filename "$f"
YML
cat > "$T/.shift-left.yml" << 'YML'
local-only:
  - id: shift-left-stamp
    reason: records that hooks ran in this clone
  - id: shift-left-stamp-pre-push
    reason: as above, for pre-push
YML
(
  cd "$T"
  git init -q -b main
  # No background maintenance or gc: after a commit git may start one that
  # holds .git/objects/maintenance.lock, and the scenarios' parallel `cp -R`
  # of this template fails when the lock vanishes mid-copy (seen in CI).
  git config maintenance.auto false
  git config gc.auto 0
  pre-commit install > /dev/null
  git add -A
  git_q commit -qm "chore: init" > /dev/null 2>&1
) || {
  echo "test-doctor: cannot build the template repo" >&2
  exit 1
}
scenario() { # scenario <name> -> fresh copy of the template, path in $R
  R="$TMP/$1"
  cp -R "$T" "$R"
  # pre-commit's hook scripts hold no repo path, so the copy's hooks work as-is
}

s1() {
  echo "Healthy:"
  scenario healthy
  doctor "$R"
  check "exits 0" test "$rc" -eq 0
  check "a line per check" says "ok +D5"
  doctor "$R" --quiet
  check "--quiet prints nothing" test -z "$out"
}

s2() {
  echo "D1 uninstalled stage (AC-SHIFT-01):"
  scenario no-commit-msg
  rm "$R/.git/hooks/commit-msg"
  doctor "$R"
  check "exits 1" test "$rc" -eq 1
  check "names the stage" says "FAIL +D1 .*commit-msg hook is not installed"
  check "and the fix" says "fix: pre-commit install$"
  check "only D1 fails" fails_only D1
  scenario foreign-hook
  echo '#!/bin/sh' > "$R/.git/hooks/pre-push"
  doctor "$R"
  check "a hook pre-commit didn't write is not 'installed'" fails_only D1
}

s3() {
  echo "D2 hook entries:"
  scenario deleted-script
  git -C "$R" rm -q scripts/lint.sh
  doctor "$R"
  check "a deleted hook script fails D2 by name" says "FAIL +D2 .*lint.*scripts/lint.sh"
  check "only D2 fails" fails_only D2
  scenario missing-tool
  sed -i.bak 's/require-tool.sh git/require-tool.sh nosuchtool/' "$R/.pre-commit-config.yaml"
  doctor "$R"
  check "a missing tool fails D2 by name (AC-SHIFT-02)" says "FAIL +D2 .*nosuchtool"
  SHIFT_LEFT_ALLOW_MISSING=nosuchtool doctor "$R"
  check "allowed: passes" test "$rc" -eq 0
  check "allowed: still listed" says "SKIPPED.*nosuchtool"
  SHIFT_LEFT_ALLOW_MISSING=nosuchtool doctor "$R" --quiet
  check "allowed: quiet stays quiet" test -z "$out"
  check "a hook no tracked file uses is not checked" bash -c "! grep -q never-applies <<< \"\$0\"" "$out"
}

s4() {
  echo "D3 pre-commit itself:"
  scenario old-pre-commit
  mkdir -p "$TMP/oldbin"
  printf '#!/usr/bin/env bash\necho "pre-commit 2.1.0"\n' > "$TMP/oldbin/pre-commit"
  chmod +x "$TMP/oldbin/pre-commit"
  out="$(cd "$R" && PATH="$TMP/oldbin:$PATH" bash scripts/shift-left/doctor.sh 2>&1)" && rc=0 || rc=$?
  check "older than minimum_pre_commit_version fails D3" says "FAIL +D3 .*2\.1\.0.*3\.0\.0"
}

s5() {
  echo "D4 config:"
  scenario bad-config
  printf 'repos: [\n' > "$R/.pre-commit-config.yaml"
  doctor "$R"
  check "an invalid config fails D4" says "FAIL +D4"
  check "and exits 1" test "$rc" -eq 1
}

s6() {
  echo "D5 stamps:"
  scenario no-verify
  echo "x = 2" > "$R/src/app.py"
  git -C "$R" add -A
  (cd "$R" && git_q commit -q --no-verify -m "feat: skip hooks") > /dev/null 2>&1
  doctor "$R"
  check "a --no-verify commit fails D5" says "FAIL +D5 .*pre-commit"
  check "only D5 fails" fails_only D5
  echo "x = 3" > "$R/src/app.py"
  git -C "$R" add -A
  (cd "$R" && git_q commit -q -m "feat: with hooks") > /dev/null 2>&1
  doctor "$R"
  check "the next normal commit clears it" test "$rc" -eq 0
}

s7() {
  echo "D5 push stamps:"
  scenario push
  git init -q --bare "$TMP/remote.git"
  git -C "$R" remote add origin "$TMP/remote.git"
  git -C "$R" push -q origin main > /dev/null 2>&1
  git -C "$R" switch -qc feature
  echo "x = 4" > "$R/src/app.py"
  git -C "$R" add -A
  (cd "$R" && git_q commit -q -m "feat: feature") > /dev/null 2>&1
  git -C "$R" push -q -u origin feature > /dev/null 2>&1
  doctor "$R"
  check "a branch pushed with hooks passes" test "$rc" -eq 0
  echo "x = 5" > "$R/src/app.py"
  git -C "$R" add -A
  (cd "$R" && git_q commit -q -m "feat: more") > /dev/null 2>&1
  git -C "$R" push -q --no-verify > /dev/null 2>&1
  doctor "$R"
  check "a --no-verify push fails D5 pre-push" says "FAIL +D5 .*pre-push"
}

# The scenarios are independent: run them at once, print them in order.
s8() {
  echo "D6 CI parity:"
  scenario no-ci-pre-commit
  sed -i.bak '/pre-commit run --all-files$/d' "$R/.github/workflows/ci.yml"
  rm "$R/.github/workflows/ci.yml.bak"
  doctor "$R"
  check "CI no longer runs the pre-commit stage: D6 names the hook" says "FAIL +D6 .*hook lint .*pre-commit"
  check "only D6 fails" fails_only D6
}

# Code-review findings: D5 must not cry wolf after normal git work.
s9() {
  echo "D5 after switching branches:"
  scenario switch
  (cd "$R" && echo 2 > src/app.py && git add -A && git_q commit -qm "feat: on main") > /dev/null 2>&1
  (cd "$R" && git switch -qc other && echo 3 > src/app.py && git add -A && git_q commit -qm "feat: on other") > /dev/null 2>&1
  git -C "$R" switch -q main
  doctor "$R"
  check "back on a branch whose commit had hooks: D5 passes" test "$rc" -eq 0
}

s10() {
  echo "D5 after a rebase:"
  scenario rebase
  (cd "$R" && git switch -qc topic && echo t > src/t.py && git add -A && git_q commit -qm "feat: topic") > /dev/null 2>&1
  (cd "$R" && git switch -q main && echo m > src/m.py && git add -A && git_q commit -qm "feat: main moves") > /dev/null 2>&1
  (cd "$R" && git switch -q topic && git_q rebase -q main) > /dev/null 2>&1
  doctor "$R"
  check "a rebased branch (rebase runs no commit hooks): D5 passes" test "$rc" -eq 0
  (cd "$R" && echo u > src/u.py && git add -A && git_q commit -q --no-verify -m "feat: skip") > /dev/null 2>&1
  doctor "$R"
  check "but a --no-verify commit on top still fails" says "FAIL +D5 .*pre-commit"
}

s11() {
  echo "D5 after other pushes:"
  scenario pushes
  git init -q --bare "$TMP/remote-pushes.git"
  git -C "$R" remote add origin "$TMP/remote-pushes.git"
  git -C "$R" push -q origin main > /dev/null 2>&1
  (cd "$R" && git switch -qc f1 && echo 1 > src/f1.py && git add -A && git_q commit -qm "feat: f1" && git push -q -u origin f1) > /dev/null 2>&1
  (cd "$R" && git switch -qc f2 main && echo 2 > src/f2.py && git add -A && git_q commit -qm "feat: f2" && git push -q -u origin f2) > /dev/null 2>&1
  git -C "$R" switch -q f1
  doctor "$R"
  check "f1 pushed with hooks, then f2 pushed: D5 still passes on f1" test "$rc" -eq 0
  (cd "$R" && echo 3 > src/f1.py && git add -A && git_q commit -qm "feat: f1 more") > /dev/null 2>&1
  touch "$R/.fail-push"
  if (cd "$R" && git push -q) > /dev/null 2>&1; then
    echo "  FAIL the push-gate hook should have blocked this push"
    return 1
  fi
  rm "$R/.fail-push"
  doctor "$R"
  check "a push its hooks blocked doesn't turn the last good push into a failure" test "$rc" -eq 0
}

s12() {
  echo "D2 for uFawkesPipe's own hooks:"
  scenario remote-hook
  # The template stands in for the pinned uFawkesPipe clone: the doctor reads
  # the manifest two levels above itself, as it would in pre-commit's cache.
  cat > "$R/.pre-commit-hooks.yaml" << 'YML'
- id: trivy
  name: dependency scan
  entry: scripts/shift-left/require-tool.sh nosuchscanner -- true
  language: script
  files: (^|/)Gemfile\.lock$
YML
  cat >> "$R/.pre-commit-config.yaml" << 'YML'
  - repo: https://github.com/paruff/uFawkesPipe
    rev: v9.9.9
    hooks:
      - id: trivy
YML
  echo "GEM" > "$R/Gemfile.lock"
  git -C "$R" add -A
  python3 -c 'import sqlite3, sys; c = sqlite3.connect(sys.argv[1]); c.execute("insert or replace into repos values (?, ?, ?)", sys.argv[2:]); c.commit()' \
    "$PRE_COMMIT_HOME/db.db" https://github.com/paruff/uFawkesPipe v9.9.9 "$R"
  doctor "$R"
  check "a remote hook's missing tool fails D2 by name" says "FAIL +D2 .*trivy.*nosuchscanner"
  check "only D2 fails" fails_only D2
}

# A scenario that dies part-way (a failed git step, set -u) is a failure, not
# a pass with fewer checks. The scenario runs under set -e and its exit status
# goes to a file. Two shapes that look right and aren't: `( set -e; "$s" ) ||`
# makes bash ignore set -e inside the scenario, and without the group's set +e
# the script's own set -e ends the group before it records the status.
SCENARIOS=(s1 s2 s3 s4 s5 s6 s7 s8 s9 s10 s11 s12)
for s in "${SCENARIOS[@]}"; do
  {
    set +e
    (
      set -e
      "$s"
    ) > "$TMP/$s.log" 2>&1
    echo $? > "$TMP/$s.rc"
  } &
done
wait
for s in "${SCENARIOS[@]}"; do
  rc="$(cat "$TMP/$s.rc")"
  [[ "$rc" == 0 ]] || echo "  FAIL scenario $s stopped early (exit $rc)" >> "$TMP/$s.log"
done
for s in "${SCENARIOS[@]}"; do cat "$TMP/$s.log"; done
fails="$(cat "$TMP"/s*.log | grep -c '^  FAIL' || true)"

cd "$HERE"
if [[ "$fails" -ne 0 ]]; then
  echo "test-doctor: $fails FAILED" >&2
  exit 1
fi
echo "test-doctor: all checks passed"
