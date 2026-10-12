#!/usr/bin/env bash
# images/ci/tests/test-release-match.sh — offline tests for `pipe-ci release-match`.
# A stub curl plays the registry; nothing here touches the network.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPE_CI="${HERE}/../entrypoints/pipe-ci"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
fails=0

ok() { echo "  ok   $1"; }
bad() {
  echo "  FAIL $1"
  fails=$((fails + 1))
}
expect() { # expect <description> <want-exit> <got-exit>
  if [[ "$3" == "$2" ]]; then ok "$1"; else bad "$1 (exit $3, want $2)"; fi
}

A=sha256:$(printf 'a%.0s' {1..64})
B=sha256:$(printf 'b%.0s' {1..64})

mkdir -p "${TMP}/bin"
cat > "${TMP}/bin/curl" << 'STUB'
#!/usr/bin/env bash
# token request -> JSON; manifest HEAD -> headers carrying STUB_DIGEST. STUB_FAIL=1: a 404.
[[ "${STUB_FAIL:-}" == 1 ]] && exit 22
case "$*" in
  *"/token?"*) echo '{"token":"t"}' ;;
  *"/manifests/"*) printf 'HTTP/2 200\r\ndocker-content-digest: %s\r\n\r\n' "${STUB_DIGEST}" ;;
  *) exit 2 ;;
esac
STUB
chmod +x "${TMP}/bin/curl"
export PATH="${TMP}/bin:${PATH}"

printf '{ "image": "ghcr.io/paruff/fawkes-space:2.0.0@sha256:abc" }\n' > "${TMP}/dc.json"
printf '{ "image": "mcr.microsoft.com/devcontainers/base:ubuntu" }\n' > "${TMP}/other.json"
printf '%s\n' "${A}" > "${TMP}/base"

run() { # run <devcontainer> [env...] -> exit code of `pipe-ci release-match`
  local dc="$1" rc=0
  shift
  env PIPE_CI_BASE_DIGEST_FILE="${TMP}/base" "$@" bash "${PIPE_CI}" release-match "${dc}" > "${TMP}/out" 2>&1 || rc=$?
  echo "${rc}"
}

echo "release-match:"
expect "same release passes" 0 "$(run "${TMP}/dc.json" STUB_DIGEST="${A}")"
expect "a different release fails" 1 "$(run "${TMP}/dc.json" STUB_DIGEST="${B}")"
grep -q "${A}" "${TMP}/out" && grep -q "${B}" "${TMP}/out" && ok "and names both digests" || bad "error does not name both digests"
expect "a registry failure is exit 67, not a pass" 67 "$(run "${TMP}/dc.json" STUB_FAIL=1 STUB_DIGEST="${A}")"
expect "a devcontainer that pins no fawkes-space is exit 67" 67 "$(run "${TMP}/other.json" STUB_DIGEST="${A}")"
expect "no devcontainer file is exit 67" 67 "$(run "${TMP}/missing.json" STUB_DIGEST="${A}")"
rc=0
env PIPE_CI_BASE_DIGEST_FILE="${TMP}/none" STUB_DIGEST="${A}" bash "${PIPE_CI}" release-match "${TMP}/dc.json" > /dev/null 2>&1 || rc=$?
expect "an image that records no base is exit 67" 67 "${rc}"
: > "${TMP}/base"
expect "an empty base file is exit 67" 67 "$(run "${TMP}/dc.json" STUB_DIGEST="${A}")"

if [[ "${fails}" -ne 0 ]]; then
  echo "test-release-match: ${fails} FAILED" >&2
  exit 1
fi
echo "test-release-match: all checks passed"
