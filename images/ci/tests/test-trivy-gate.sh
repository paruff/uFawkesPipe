#!/usr/bin/env bash
# images/ci/tests/test-trivy-gate.sh — offline tests for trivy-gate.sh.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="${HERE}/trivy-gate.sh"
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

printf 'semgrep==1.179.0 \\\n    --hash=sha256:aa\nrequests==2.32.0 \\\n    --hash=sha256:bb\n' > "${TMP}/lock"
vuln() { # vuln <id> <package> -> one Trivy vulnerability object
  printf '{"VulnerabilityID":"%s","PkgName":"%s","InstalledVersion":"1","FixedVersion":"2","Severity":"HIGH"}' "$1" "$2"
}
result() { # result <target> <type> <vuln>... -> one Trivy result object
  local target="$1" type="$2"
  shift 2
  printf '{"Target":"%s","Type":"%s","Vulnerabilities":[%s]}' "${target}" "${type}" "$(
    IFS=,
    echo "$*"
  )"
}
report() { printf '{"Results":[%s]}' "$(
  IFS=,
  echo "$*"
)" > "${TMP}/t.json"; }
exceptions() { printf '[{"id":"%s","target":"%s","reason":"r","expires":"%s"}]' "$1" "$2" "$3" > "${TMP}/ex.json"; }
gate() { # gate [env...] -> exit code of the gate on t.json
  local rc=0
  env "$@" bash "${GATE}" "${TMP}/t.json" "${TMP}/ex.json" "${TMP}/lock" > /dev/null 2>&1 || rc=$?
  echo "${rc}"
}
COMPOSE=usr/local/lib/docker/cli-plugins/docker-compose

echo "Gate:"
exceptions CVE-0 none 2099-01-01
report "$(result "${COMPOSE}" gobinary "$(vuln CVE-1 stdlib)")"
expect "a finding in docker compose with no exception fails" 1 "$(gate X=1)"
exceptions CVE-1 "${COMPOSE}" 2099-01-01
expect "an exception for that CVE and target covers it" 0 "$(gate X=1)"
exceptions CVE-1 "${COMPOSE}" 2026-01-01
expect "an expired exception stops covering: the gate is back on" 1 "$(gate GATE_TODAY=2026-06-01)"
exceptions CVE-1 "${COMPOSE}" 2099-01-01
expect "an exception is for one target: same CVE elsewhere is not covered" 1 \
  "$(report "$(result usr/local/bin/docker gobinary "$(vuln CVE-1 stdlib)")" && gate X=1)"
report "$(result usr/local/bin/gitleaks gobinary "$(vuln CVE-9 stdlib)")" "$(result "ufawkes-ci:ci (debian 13.7)" debian "$(vuln CVE-8 openssl)")"
expect "findings in fawkes-core's tools and the Debian base are reported, not gated" 0 "$(gate X=1)"
for tool in terraform tflint kubectl helm kubeconform kustomize argocd; do
  report "$(result "usr/local/bin/${tool}" gobinary "$(vuln CVE-7 stdlib)")"
  expect "a finding in ${tool} is reported, not gated" 0 "$(gate X=1)"
done
report "$(result "Python" python-pkg "$(vuln CVE-2 semgrep)")"
expect "a Python package in semgrep's lock is gated" 1 "$(gate X=1)"
report "$(result "Python" python-pkg "$(vuln CVE-3 pre-commit)")"
expect "a Python package that is not in semgrep's lock is not" 0 "$(gate X=1)"
report "$(result opt/ufawkes-runner/bin/Runner.Listener.dll dotnet-core "$(vuln CVE-4 System.Net)")"
expect "the Actions runner is gated" 1 "$(gate X=1)"
report "$(result "${COMPOSE}" gobinary "$(vuln CVE-5 stdlib)")"
rc=0
bash "${GATE}" "${TMP}/t.json" "${TMP}/ex.json" "${TMP}/lock" --report-only > /dev/null 2>&1 || rc=$?
expect "--report-only prints the finding and exits 0" 0 "${rc}"
printf '{"Results":[]}' > "${TMP}/t.json"
expect "no findings passes" 0 "$(gate X=1)"

if [[ "${fails}" -ne 0 ]]; then
  echo "test-trivy-gate: ${fails} FAILED" >&2
  exit 1
fi
echo "test-trivy-gate: all checks passed"
