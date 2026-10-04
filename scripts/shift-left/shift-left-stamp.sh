#!/usr/bin/env bash
# scripts/shift-left-stamp.sh — record that a hook stage ran, and on what
# (shift-left spec R5, D5). Run as the last, always-run hook of each stage;
# scripts/doctor.sh compares the stamp with the commit or push it belongs to.
#
# Usage: shift-left-stamp.sh <pre-commit|pre-push>
#   pre-commit stamps the tree about to be committed (`git write-tree`);
#   pre-push stamps the tree of the commit being pushed.
# A stamp means the hooks ran on that content, not that they passed: a failed
# run blocks the commit, and CI catches a --no-verify after one.
#
# Each stage's file is a set of trees (the last 500), not one: switching
# branches, pushing another branch, or a run whose hooks failed must not make a
# tree that did go through the hooks look as if it hadn't.
set -euo pipefail

stage="${1:?usage: shift-left-stamp.sh <pre-commit|pre-push>}"
case "$stage" in
  pre-commit) tree="$(git write-tree)" ;;
  pre-push) tree="$(git rev-parse "${PRE_COMMIT_TO_REF:-HEAD}^{tree}")" ;;
  *)
    echo "shift-left-stamp: unknown stage $stage" >&2
    exit 2
    ;;
esac
dir="$(git rev-parse --git-path shift-left)"
mkdir -p "$dir"
echo "$tree" >> "$dir/$stage"
tail -n 500 "$dir/$stage" > "$dir/$stage.tmp" && mv "$dir/$stage.tmp" "$dir/$stage"
