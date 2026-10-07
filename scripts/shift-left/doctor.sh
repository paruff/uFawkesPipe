#!/usr/bin/env bash
# scripts/shift-left/doctor.sh — are this clone's checks actually running?
# (uFawkes.dev docs/ai-sdlc/shift-left/spec.md R5). Read-only. A repo runs it
# through its shim: `bash scripts/shift-left.sh doctor` (make doctor).
#
#   D1  every hook stage the config installs is in .git/hooks, written by pre-commit
#   D2  every hook that applies here resolves: its script exists and is
#       executable, its system tool is on PATH, its require-tool.sh tool is installed.
#       uFawkesPipe's own hooks are read from the manifest beside this script.
#   D3  pre-commit is installed and meets minimum_pre_commit_version
#   D4  the config validates and the remote hook environments are installed
#   D5  the last local commit, and the last push of this branch, went through
#       their hooks: its tree is in the stage's stamps (scripts/shift-left-stamp.sh).
#       Only a commit `git commit` made is judged: rebase, merge, cherry-pick and
#       revert run no commit hooks, and the commits they replay already did.
#   D6  every hook runs in CI, or .shift-left.yml says why not
#       (check-shift-left-parity.sh, beside this script)
#   D7  the hook job is a required check on the default branch, so a red hook
#       run blocks the merge. Read from the repo's effective rules through gh;
#       skipped, with a note, when there's no GitHub remote, gh isn't
#       authenticated, or the API can't be read (a laptop offline is not a fault).
#
# One line per check, a fix under each failure. --quiet prints only failures,
# so it can run at every session start without noise. Exit 1 on any failure.
set -uo pipefail

QUIET=""
# The pinned uFawkesPipe clone (or uFawkesPipe itself) this script runs from.
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ "${1:-}" == "--quiet" ]] && QUIET=1
cd "$(git rev-parse --show-toplevel 2> /dev/null)" || {
  echo "doctor: not in a git repository" >&2
  exit 1
}
CONFIG=.pre-commit-config.yaml
failed=0
ok() { [[ -n "$QUIET" ]] || printf '  ok    %s  %s\n' "$1" "$2"; }
note() { [[ -n "$QUIET" ]] || printf '  note  %s  %s\n' "$1" "$2"; }
fail() {
  printf '  FAIL  %s  %s\n        fix: %s\n' "$1" "$2" "$3"
  failed=1
}
finish() {
  if [[ "$failed" -ne 0 ]]; then
    echo "doctor: problems found. Until they're fixed, checks you think ran may not have."
    exit 1
  fi
  exit 0
}

# --- D3, D4: the prerequisites everything else reads -------------------------
if ! command -v pre-commit > /dev/null; then
  fail D3 "pre-commit is not installed" "pip install pre-commit (or: make pre-commit-setup)"
  finish
fi
if [[ ! -f "$CONFIG" ]]; then
  fail D4 "no $CONFIG" "start from uFawkesPipe's $CONFIG"
  finish
fi
if ! err="$(pre-commit validate-config "$CONFIG" 2>&1)"; then
  fail D4 "$CONFIG is invalid: $(head -3 <<< "$err" | tr '\n' ' ')" "pre-commit validate-config $CONFIG"
  finish
fi

# Everything the checks need from the config, one fact per line (tab-separated).
facts="$(git ls-files | python3 -c '
import os, re, sys, yaml
cfg = yaml.safe_load(open(sys.argv[1])) or {}
manifest_path = sys.argv[2]
manifest = {h["id"]: h for h in (yaml.safe_load(open(manifest_path)) or [])} if os.path.exists(manifest_path) else {}
is_pipe = lambda url: str(url).lower().rstrip("/").removesuffix(".git").endswith("paruff/ufawkespipe")
files = sys.stdin.read().splitlines()
print("min\t%s" % cfg.get("minimum_pre_commit_version", ""))
for s in cfg.get("default_install_hook_types") or ["pre-commit"]:
    print("stage\t%s" % s)
top_ex = cfg.get("exclude") or "^$"
for repo in cfg.get("repos") or []:
    if repo["repo"] not in ("local", "meta"):
        print("remote\t%s\t%s" % (repo["repo"], repo.get("rev", "")))
    for h in repo.get("hooks") or []:
        print("hookid\t%s" % h["id"])
        if is_pipe(repo["repo"]) and h["id"] in manifest:
            h = {**manifest[h["id"]], **h}  # the repo\x27s config overrides the manifest
        elif repo["repo"] != "local":
            continue
        inc, exc = re.compile(h.get("files", "")), re.compile(h.get("exclude", "^$"))
        applies = h.get("always_run") or any(
            inc.search(f) and not exc.search(f) and not re.search(top_ex, f) for f in files)
        if not applies:
            continue
        words = h["entry"].split()
        tool = words[1] if words[0].endswith("require-tool.sh") and len(words) > 1 else "-"
        # A remote hook\x27s script lives in its clone, not here: only its tool is checked.
        lang = h.get("language", "") if repo["repo"] == "local" else "remote"
        print("hook\t%s\t%s\t%s\t%s" % (h["id"], lang, words[0], tool))
' "$CONFIG" "$here/../../.pre-commit-hooks.yaml" 2>&1)" || {
  fail D4 "cannot read $CONFIG: $facts" "python3 needs PyYAML: pip install pyyaml"
  finish
}
field() { awk -F'\t' -v k="$1" '$1==k' <<< "$facts"; }

have="$(pre-commit --version 2> /dev/null | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)"
min="$(field min | cut -f2)"
if [[ -n "$min" && "$(printf '%s\n%s\n' "$min" "$have" | sort -V | head -1)" != "$min" ]]; then
  fail D3 "pre-commit $have is older than minimum_pre_commit_version $min" "pip install -U pre-commit"
else
  ok D3 "pre-commit $have${min:+ (minimum $min)}"
fi

db="${PRE_COMMIT_HOME:-${XDG_CACHE_HOME:-$HOME/.cache}/pre-commit}/db.db"
missing_envs="$(field remote | python3 -c '
import os, sqlite3, sys
db = sys.argv[1]
have = set()
if os.path.exists(db):
    have = set(sqlite3.connect(db).execute("select repo, ref from repos"))
for line in sys.stdin.read().splitlines():
    _, repo, rev = line.split("\t")
    if (repo, rev) not in have:
        print(repo.rsplit("/", 1)[-1] + "@" + rev)
' "$db")"
if [[ -n "$missing_envs" ]]; then
  fail D4 "hook environments not installed: $(tr '\n' ' ' <<< "$missing_envs")" "pre-commit install-hooks"
else
  ok D4 "config valid; hook environments installed"
fi

# --- D1: installed stages ----------------------------------------------------
hooks_dir="$(git rev-parse --git-path hooks)"
d1=0
while read -r stage; do
  if ! grep -q "File generated by pre-commit" "$hooks_dir/$stage" 2> /dev/null; then
    fail D1 "the $stage hook is not installed, so that stage never runs" "pre-commit install"
    d1=1
  fi
done < <(field stage | cut -f2)
[[ "$d1" -eq 0 ]] && ok D1 "hook stages installed: $(field stage | cut -f2 | paste -sd ' ' -)"

# --- D2: hook entries --------------------------------------------------------
d2=0
n=0
while IFS=$'\t' read -r _ id lang cmd tool; do
  n=$((n + 1))
  if [[ "$lang" == script && ! -x "$cmd" ]]; then
    fail D2 "hook $id: $cmd is missing or not executable" "restore $cmd, or remove the hook"
    d2=1
  elif [[ "$lang" == system ]] && ! command -v "$cmd" > /dev/null; then
    fail D2 "hook $id: $cmd is not on PATH" "install $cmd"
    d2=1
  fi
  if [[ "$tool" != - ]] && ! command -v "$tool" > /dev/null; then
    if [[ ",${SHIFT_LEFT_ALLOW_MISSING:-}," == *",$tool,"* ]]; then
      note D2 "SKIPPED (tool missing): $tool, for hook $id (SHIFT_LEFT_ALLOW_MISSING)"
    else
      fail D2 "hook $id: $tool is not installed, so the hook fails" "install $tool, or SHIFT_LEFT_ALLOW_MISSING=$tool to skip it knowingly"
      d2=1
    fi
  fi
done < <(field hook)
[[ "$d2" -eq 0 ]] && ok D2 "$n hook entries that apply here resolve"

# --- D5: stamps ----------------------------------------------------------------
stamps="$(git rev-parse --git-path shift-left)"
d5=0
has_hook() { field hookid | cut -f2 | grep -qx "$1"; }
if ! has_hook shift-left-stamp; then
  fail D5 "no shift-left-stamp hook, so nothing records that hooks ran" "add the shift-left-stamp hooks from uFawkesPipe (.pre-commit-hooks.yaml)"
  d5=1
elif git rev-parse -q --verify HEAD > /dev/null && [[ -z "$(git branch -r --contains HEAD 2> /dev/null)" ]]; then
  # Only a commit not yet on any remote (pushed commits had CI), and only one
  # `git commit` made: the reflog's oldest entry for HEAD says what created it.
  head="$(git rev-parse HEAD)"
  made_by="$(git reflog --format='%H %gs' 2> /dev/null | awk -v h="$head" '$1 == h { s = $2 } END { print s }')"
  if [[ "$made_by" == commit* ]] && ! grep -qxF "$(git rev-parse 'HEAD^{tree}')" "$stamps/pre-commit" 2> /dev/null; then
    fail D5 "the last commit ($(git log -1 --format='%h %s')) never went through the pre-commit hooks" "pre-commit run --all-files (re-checks it and re-stamps)"
    d5=1
  fi
fi
if has_hook shift-left-stamp-pre-push && up="$(git rev-parse -q --abbrev-ref '@{u}' 2> /dev/null)"; then
  remote="${up%%/*}"
  base="$(git symbolic-ref -q --short "refs/remotes/$remote/HEAD" || echo "$remote/main")"
  # Only a pushed branch with its own commits; the default branch is merged by GitHub.
  if git rev-parse -q --verify "$base" > /dev/null && [[ "$(git rev-list --count "$base..$up")" -gt 0 ]] \
    && ! grep -qxF "$(git rev-parse "$up^{tree}")" "$stamps/pre-push" 2> /dev/null; then
    fail D5 "the last push of $up didn't go through the pre-push hooks" "pre-commit run --hook-stage pre-push --all-files, then push again"
    d5=1
  fi
fi
[[ "$d5" -eq 0 ]] && ok D5 "the last commit and push went through their hooks"

# --- D6: CI parity -------------------------------------------------------------
if [[ ! -x "$here/check-shift-left-parity.sh" ]]; then
  fail D6 "no check-shift-left-parity.sh beside the doctor, so nothing checks that CI runs these hooks" "pin a uFawkesPipe release that has it"
elif parity="$(bash "$here/check-shift-left-parity.sh" 2>&1)"; then
  ok D6 "${parity#parity: }"
else
  while read -r line; do
    fail D6 "${line#FAIL }" "run that stage in CI, or list the hook in .shift-left.yml with a reason"
  done < <(grep '^FAIL' <<< "$parity" || echo "FAIL $parity")
fi

# --- D7: the hook job is a required check -------------------------------------
# The check is named after the Pre-flight / pre-commit job, whatever the repo
# calls it (e.g. "Pre-flight / Pre-flight Checks", "Pre-commit hooks / ...").
d7_note() { note D7 "skipped: $1"; }
slug="$(git remote get-url origin 2> /dev/null | sed -nE 's#^(https://github\.com/|git@github\.com:)##p' | sed -E 's#/$##; s#\.git$##')"
if [[ -z "$slug" ]]; then
  d7_note "no GitHub origin remote"
elif ! command -v gh > /dev/null || ! gh auth status > /dev/null 2>&1; then
  d7_note "gh isn't authenticated, so required checks can't be read (gh auth login)"
else
  branch="$(gh api "repos/$slug" --jq .default_branch 2> /dev/null || true)"
  branch="${branch:-main}"
  if ! rules="$(gh api "repos/$slug/rules/branches/$branch" 2> /dev/null)"; then
    d7_note "couldn't read the rules of $slug@$branch"
  else
    required="$(python3 -c '
import json, sys
for rule in json.load(sys.stdin):
    if rule.get("type") == "required_status_checks":
        for c in rule["parameters"]["required_status_checks"]:
            print(c["context"])
' <<< "$rules" 2> /dev/null)"
    if grep -qiE 'pre-?flight|pre-?commit' <<< "$required"; then
      ok D7 "$slug@$branch requires the hook job ($(grep -iE 'pre-?flight|pre-?commit' <<< "$required" | head -1))"
    else
      fail D7 "$slug@$branch doesn't require the hook job, so a red hook run doesn't block a merge" "add the Pre-flight / pre-commit job to the required status checks of the $branch ruleset (Settings > Rules)"
    fi
  fi
fi

finish
