#!/usr/bin/env bash
# scripts/shift-left/reinstall-hooks.sh — install the git hook for every stage the
# hook config lists, when a checkout or merge brought in a config that lists one
# that isn't installed (shift-left plan G, uFawkesPipe#150).
#
# `pre-commit install` is never re-run when the config changes, so a stage added
# later (pre-push, say) stays uninstalled in every existing clone until someone
# remembers to; the doctor reports it (D1), but nothing repaired it. Run as the
# shift-left-reinstall hook at post-checkout and post-merge: both fire after the
# new config is on disk, and `pre-commit install` reads default_install_hook_types.
#
# Silent unless it installed something. It never fails the checkout or merge:
# a post-checkout hook's exit status would become git's own, and a repair that
# can't run is a warning, not a reason to stop someone switching branches.
set -uo pipefail

root="$(git rev-parse --show-toplevel 2> /dev/null)" || exit 0
cd "$root" || exit 0
[[ -f .pre-commit-config.yaml ]] || exit 0
command -v pre-commit > /dev/null || exit 0

hooks="$(git rev-parse --git-path hooks)"
installed() {
  local f
  for f in "$hooks"/*; do
    [[ -e "$f" && "$f" != *.sample ]] && basename "$f"
  done | sort
}
before="$(installed)"
if ! out="$(pre-commit install 2>&1)"; then
  echo "shift-left: pre-commit install failed, so a newly listed hook stage may not be installed: ${out##*$'\n'}" >&2
  exit 0
fi
added="$(comm -13 <(printf '%s\n' "$before") <(printf '%s\n' "$(installed)") | paste -sd, - | sed 's/,/, /g')"
[[ -n "$added" ]] && echo "shift-left: installed the $added git hook (the hook config lists it)"
exit 0
