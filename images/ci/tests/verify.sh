#!/usr/bin/env bash
# images/ci/tests/verify.sh <image-ref> — acceptance checks for ufawkes-ci
# (docs/ci-runner-image/spec.md R3, AC2, AC9). Run against the image just built
# and again against the digest just pushed. Needs Docker; every check that must
# work offline runs with --network none. Exits non-zero if any check fails.
set -euo pipefail

IMAGE="${1:?usage: verify.sh <image-ref>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fails=0

ok() { echo "  ok   $1"; }
bad() {
  echo "  FAIL $1"
  fails=$((fails + 1))
}
expect() { # expect <description> <want-exit> <got-exit>
  if [[ "$3" == "$2" ]]; then ok "$1"; else bad "$1 (exit $3, want $2)"; fi
}

echo "Manifest (R3): core's entries are all kept, the CI entries are added"
base="$(awk '/^FROM .* AS base$/ {print $2}' "${HERE}/../Dockerfile")"
names() { docker run --rm "$1" jq -r '.[].name' /etc/ufawkes/tools.json | sort; }
core="$(names "${base}")"
img="$(names "${IMAGE}")"
missing="$(comm -23 <(echo "${core}") <(echo "${img}") | tr '\n' ' ')"
[[ -z "${missing}" ]] && ok "no core entry missing" || bad "core entries missing: ${missing}"
for n in actions-runner docker-cli docker-compose semgrep semgrep-rules; do
  grep -qx "${n}" <<< "${img}" && ok "manifest has ${n}" || bad "manifest lacks ${n}"
done

echo "Runner entrypoint (AC9)"
rc=0
out="$(docker run --rm -e RUNNER_REPO_URL=https://x -e RUNNER_NAME=x "${IMAGE}" runner.sh 2>&1)" || rc=$?
expect "missing env exits 2" 2 "${rc}"
grep -q "RUNNER_TOKEN" <<< "${out}" && ok "and names RUNNER_TOKEN" || bad "stderr does not name RUNNER_TOKEN"
rc=0
docker run --rm -e RUNNER_REPO_URL=https://invalid.example.invalid -e RUNNER_TOKEN=t -e RUNNER_NAME=x \
  "${IMAGE}" runner.sh > /dev/null 2>&1 || rc=$?
expect "failed registration exits 3, never reaches run.sh" 3 "${rc}"

# The in-container checks below run with no network at all (AC2).
offline() { docker run --rm --network none -i "${IMAGE}" bash -s; }

echo "pipe-ci security, offline (AC2, AC9-iii)"
out="$(
  offline << 'SH'
set -u
git config --global user.email t@t
git config --global user.name t
git config --global init.defaultBranch main
mk() { mkdir -p "/w/$1" && cd "/w/$1" && git init -q; }
mk bad
# The key header is assembled at run time, so this file holds no literal private-key
# marker for the repo's own secret scanners to flag.
b=BEGIN
e=END
printf -- '-----%s RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAyE3pQZrJ0q8mWb2m3kqQw1gT0s7yq5VxkP8fL2N9aB4cD6eF\n8gH1iJ3kL5mN7oP9qR2sT4uV6wX8yZ0aB3cD5eF7gH9iJ1kL3mN5oP7qR9sT1uV3\nwX5yZ7aB9cD1eF3gH5iJ7kL9mN1oP3qR5sT7uV9wX1yZ3aB5cD7eF9gH1iJ3kL5\n-----%s RSA PRIVATE KEY-----\n' "$b" "$e" > key.pem
git add -A && git commit -qm init
pipe-ci security > /dev/null 2>&1
echo "secret=$?"
mk clean
printf '# hello\n\nA clean repo.\n' > README.md
printf 'a: 1\n' > c.yaml
git add -A && git commit -qm init
pipe-ci security > /dev/null 2>&1
echo "clean=$?"
pipe-ci pre-commit --baseline > /dev/null 2>&1
echo "baseline=$?"
mkdir -p /w/inj/.github/workflows && cd /w/inj
printf 'on: issues\njobs:\n  j:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo "${{ github.event.issue.title }}"\n' > .github/workflows/x.yml
semgrep scan --config /opt/ufawkes/semgrep-rules --error --metrics=off --disable-version-check --quiet . > /dev/null 2>&1
echo "injection=$?"
SH
)"
get() { sed -n "s/^$1=//p" <<< "${out}"; }
expect "a committed private key makes security fail" 1 "$(get secret)"
expect "a clean repo passes security" 0 "$(get clean)"
expect "a clean repo passes the baseline hooks" 0 "$(get baseline)"
expect "the vendored ruleset flags a workflow injection" 1 "$(get injection)"

if [[ "${fails}" -ne 0 ]]; then
  echo "verify.sh: ${fails} FAILED" >&2
  exit 1
fi
echo "verify.sh: all checks passed"
