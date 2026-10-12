#!/usr/bin/env bash
# images/ci/tests/trivy-gate.sh <trivy.json> <exceptions.json> <requirements.lock> [--report-only]
#
# The Trivy gate for ufawkes-ci. Like uFawkesAI's, it gates what this repo
# controls and only reports the rest: fawkes-core's own tools and the Debian
# base are fixed by core's rebuild, not here.
#
# Gated: docker CLI, docker compose, the Actions runner, and the Python
# packages in the semgrep lock. Reported, not gated: the infrastructure tools (terraform,
# tflint, kubectl, helm, kubeconform, kustomize, argocd) and the supply-chain tools (syft,
# conftest, cosign). They are third-party Go binaries kept
# at their newest release, and what remains is upstream's to fix. A finding there fails unless exceptions.json
# lists its CVE and target with an `expires` date that has not passed; an
# expired exception stops covering, so the gate comes back on by itself.
# --report-only prints and exits 0 (pull requests).
set -euo pipefail

json="${1:?usage: trivy-gate.sh <trivy.json> <exceptions.json> <requirements.lock> [--report-only]}"
exceptions="${2:?exceptions.json}"
lock="${3:?requirements.lock}"
report_only="${4:-}"
today="${GATE_TODAY:-$(date -u +%Y-%m-%d)}"

# Package names of the semgrep closure, lower-cased: `name==version \` lines.
pkgs="$(grep -oE '^[A-Za-z0-9_.-]+==' "${lock}" | tr -d '=' | tr '[:upper:]' '[:lower:]' | jq -R . | jq -s .)"

# One line per gated finding: id, target, package, installed, fixed, covered?
findings="$(jq -r --argjson pkgs "${pkgs}" --slurpfile ex "${exceptions}" --arg today "${today}" '
  def gated($r): ($r.Target == "usr/local/bin/docker")
    or ($r.Target == "usr/local/lib/docker/cli-plugins/docker-compose")
    or ($r.Target | startswith("opt/ufawkes-runner/"))
    or ($r.Type == "python-pkg");
  .Results[]? as $r
  | select(gated($r))
  | $r.Vulnerabilities[]?
  | select($r.Type != "python-pkg" or ((.PkgName | ascii_downcase) as $n | $pkgs | index($n)))
  | . as $v
  | ($ex[0] | map(select(.id == $v.VulnerabilityID and .target == $r.Target and .expires >= $today)) | length > 0) as $covered
  | [$v.VulnerabilityID, $r.Target, $v.PkgName, $v.InstalledVersion, ($v.FixedVersion // "-"), (if $covered then "excepted" else "FAIL" end)]
  | @tsv' "${json}")"

if [[ -z "${findings}" ]]; then
  echo "trivy-gate: no findings in what this image adds"
  exit 0
fi
echo "trivy-gate: findings in what this image adds (CVE, target, package, installed, fixed, status):"
echo "${findings}"
if grep -q "FAIL$" <<< "${findings}"; then
  if [[ "${report_only}" == "--report-only" ]]; then
    echo "trivy-gate: report-only: not failing"
    exit 0
  fi
  echo "trivy-gate: uncovered findings above" >&2
  exit 1
fi
