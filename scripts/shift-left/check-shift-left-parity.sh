#!/usr/bin/env bash
# scripts/check-shift-left-parity.sh — every configured hook runs in CI, or
# .shift-left.yml says why not (docs/ai-sdlc/shift-left/spec.md R3, D6).
#
# CI runs the hooks with the same command a laptop does (`pre-commit run
# --all-files`, per stage), so a new hook needs no workflow edit. What can
# drift is the set of stages CI runs: a hook whose stages CI never runs, and
# that isn't in .shift-left.yml, fails here. The stages CI runs are read from
# the `pre-commit run` lines in .github/workflows/*.yml (--all-files required;
# commit-msg needs --commit-msg-filename instead). A call to uFawkesPipe's
# reusable-preflight.yml counts as all three stages: that is what it runs.
#
# .shift-left.yml:
#   local-only: [{id, reason}]  runs on a laptop, skipped in CI
#   ci-only:    [{id, reason}]  stages: [manual], run in CI with --hook-stage manual
#
# Usage: check-shift-left-parity.sh                 report; exit 1 on drift
#        check-shift-left-parity.sh --skip-list <stage>
#            the SKIP= value for CI at that stage: local-only hooks, and at
#            pre-push the hooks that already ran at pre-commit
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

exec python3 - "$@" << 'PY'
import glob, os, re, sys, yaml

LEGACY = {"commit": "pre-commit", "push": "pre-push", "merge-commit": "pre-merge-commit"}
norm = lambda stages: [LEGACY.get(s, s) for s in stages]

cfg = yaml.safe_load(open(".pre-commit-config.yaml")) or {}
default = norm(cfg.get("default_stages") or ["pre-commit"])
hooks = []  # (id, stages) in config order
for repo in cfg.get("repos") or []:
    for h in repo.get("hooks") or []:
        # ponytail: a remote hook without `stages` is assumed to use default_stages;
        # its manifest could say otherwise. Read the manifest if that ever matters.
        hooks.append((h["id"], norm(h.get("stages") or default)))
ids = {i for i, _ in hooks}

sl = yaml.safe_load(open(".shift-left.yml")) if os.path.exists(".shift-left.yml") else {}
sl = sl or {}
errors = []
lists = {}
for kind in ("local-only", "ci-only"):
    lists[kind] = {}
    for e in sl.get(kind) or []:
        i = (e or {}).get("id", "?")
        if not (e or {}).get("reason"):
            errors.append(f"{i}: its .shift-left.yml {kind} entry has no reason")
        if i not in ids:
            errors.append(f"{i}: listed in .shift-left.yml {kind}, but no hook has that id")
        lists[kind][i] = e.get("reason") if e else None
local_only, ci_only = lists["local-only"], lists["ci-only"]

ci_stages = set()
REUSABLE = re.compile(r"uses:\s*paruff/ufawkespipe/\.github/workflows/reusable-preflight\.ya?ml@", re.I)
for wf in sorted(glob.glob(".github/workflows/*.y*ml")):
    for line in open(wf):
        line = line.split("#", 1)[0]
        if REUSABLE.search(line):
            ci_stages |= {"pre-commit", "pre-push", "commit-msg"}
            continue
        if "pre-commit run" not in line:
            continue
        m = re.search(r"--hook-stage[ =](\S+)", line)
        stage = LEGACY.get(m.group(1), m.group(1)) if m else "pre-commit"
        if stage == "commit-msg" and "--commit-msg-filename" in line:
            ci_stages.add(stage)
        elif stage != "commit-msg" and "--all-files" in line:
            ci_stages.add(stage)

args = sys.argv[1:]
if args[:1] == ["--skip-list"]:
    stage = args[1]
    skip = set(local_only)
    if stage == "pre-push":
        skip |= {i for i, st in hooks if "pre-push" in st and "pre-commit" in st}
    print(",".join(sorted(skip)))
    sys.exit(0)

for i, stages in hooks:
    if i in local_only:
        continue
    if i in ci_only:
        if "manual" not in stages:
            errors.append(f"{i}: ci-only hooks run with --hook-stage manual, so give it stages: [manual]")
        elif "manual" not in ci_stages:
            errors.append(f"{i}: ci-only, but no workflow runs pre-commit --hook-stage manual --all-files")
        continue
    if not set(stages) & ci_stages:
        errors.append(
            f"hook {i} ({', '.join(stages)}) never runs in CI: run that stage in CI "
            f"(pre-commit run --all-files --hook-stage <stage>), or list it in .shift-left.yml "
            f"under local-only with a reason")

for e in errors:
    print(f"FAIL {e}")
if errors:
    sys.exit(1)
n_local = sum(1 for i, _ in hooks if i in local_only)
n_ci_only = sum(1 for i, _ in hooks if i in ci_only)
extra = f", {n_ci_only} ci-only" if n_ci_only else ""
print(f"parity: {len(hooks)} hooks: {len(hooks) - n_local - n_ci_only} run in CI, {n_local} local-only{extra}"
      f" (CI runs: {', '.join(sorted(ci_stages))})")
PY
