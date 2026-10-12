#!/usr/bin/env bash
# scripts/suite-bump.sh <release-tag> [--dry-run] [repo...]
# Move every suite repo to one uFawkesPipe release (ci-pipeline spec R3): rewrites each
# `uses: paruff/uFawkesPipe/.github/workflows/<file>@<sha>` to the SHA of <release-tag>
# and opens one PR per repo that changed. --dry-run clones and rewrites but pushes
# nothing and prints each repo's diff. Default repos: the seven of the suite.
#
#   scripts/suite-bump.sh --rewrite <sha> <tag> <file>...   rewrite files in place (tests)
set -euo pipefail

OWNER="${BUMP_OWNER:-paruff}"
PIPE="${BUMP_PIPE_REPO:-uFawkesPipe}"
DEFAULT_REPOS=(uFawkes.dev uFawkesAI uFawkesObs uFawkesPipe uFawkesDevX uFawkesDojo fawkes)

die() {
  echo "suite-bump: $*" >&2
  exit 1
}

# rewrite <sha> <tag> <file>... -> prints the files that changed
rewrite() {
  local sha="$1" tag="$2"
  shift 2
  python3 - "${sha}" "${tag}" "$@" << 'PY'
import re, sys
sha, tag, files = sys.argv[1], sys.argv[2], sys.argv[3:]
# Matches the repo name in any case (uFawkesPipe / ufawkespipe), an optional trailing "# comment".
pat = re.compile(r"(paruff/ufawkespipe/\.github/workflows/[A-Za-z0-9._-]+@)[0-9a-f]{40}([ \t]*#[^\n]*)?", re.I)
for f in files:
    s = open(f).read()
    new = pat.sub(lambda m: f"{m.group(1)}{sha} # {tag}", s)
    if new != s:
        open(f, "w").write(new)
        print(f)
PY
}

if [[ "${1:-}" == "--rewrite" ]]; then
  shift
  rewrite "$@"
  exit 0
fi

tag="${1:?usage: suite-bump.sh <release-tag> [--dry-run] [repo...]}"
shift
dry=0
if [[ "${1:-}" == "--dry-run" ]]; then
  dry=1
  shift
fi
repos=("$@")
[[ ${#repos[@]} -gt 0 ]] || repos=("${DEFAULT_REPOS[@]}")

command -v gh > /dev/null || die "gh is required"
# The tag may be annotated: dereference to the commit.
sha="$(gh api "repos/${OWNER}/${PIPE}/commits/${tag}" --jq .sha)" || die "cannot resolve ${tag} in ${OWNER}/${PIPE}"
[[ "${sha}" =~ ^[0-9a-f]{40}$ ]] || die "${tag} did not resolve to a commit SHA: ${sha}"
echo "suite-bump: ${tag} = ${sha}"

work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT
for repo in "${repos[@]}"; do
  [[ "${repo}" == "${PIPE}" ]] && {
    echo "== ${repo}: skipped (calls its own reusables by ./ path)"
    continue
  }
  echo "== ${repo}"
  gh repo clone "${OWNER}/${repo}" "${work}/${repo}" -- --depth 1 -q || die "cannot clone ${repo}"
  cd "${work}/${repo}"
  mapfile -t files < <(git ls-files '.github/workflows/*.yml' '.github/workflows/*.yaml')
  [[ ${#files[@]} -gt 0 ]] || {
    echo "   no workflows"
    cd - > /dev/null
    continue
  }
  changed="$(rewrite "${sha}" "${tag}" "${files[@]}")"
  if [[ -z "${changed}" ]]; then
    echo "   already on ${tag} (or calls no Pipe reusable)"
    cd - > /dev/null
    continue
  fi
  git --no-pager diff --stat | sed 's/^/   /'
  if [[ "${dry}" == 1 ]]; then
    git --no-pager diff -U0 | sed -n '/^[-+].*[uU][fF]awkes[pP]ipe/p' | sed 's/^/   /' | head -12
    cd - > /dev/null
    continue
  fi
  branch="chore/bump-pipe-${tag}"
  git checkout -q -b "${branch}"
  git commit -q -am "chore(ci): bump uFawkesPipe reusables to ${tag}" \
    -m "One pipeline, versioned once (ci-pipeline spec R3): every suite repo calls Pipe's reusables at the SHA of ${tag} (${sha})."
  git push -q -u origin "${branch}"
  gh pr create --head "${branch}" --base main --title "chore(ci): bump uFawkesPipe reusables to ${tag}" \
    --body "Moves this repo's calls of uFawkesPipe's reusable workflows to ${tag} (\`${sha}\`), part of the suite-wide bump (ci-pipeline spec R3)."
  cd - > /dev/null
done
