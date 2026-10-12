# ufawkes-ci: the suite's CI image (docs/ci-runner-image/spec.md).
# Layered on the published fawkes-core, never rebuilt here (spec R1).
# fawkes-core 2.0.0; bump together with uFawkesAI's next CDE release (R4).
FROM ghcr.io/paruff/fawkes-core@sha256:15a466e07a59dab4863622e6eeca19c748b3018081c85771b0f01acbeffc29bd AS base

# Fetch every download and verify it against runner.lock. A mismatch fails
# the build (spec R3); nothing here is trusted by version alone.
FROM base AS fetch
ARG TARGETARCH
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]
COPY runner.lock /runner.lock
RUN <<'SH'
set -euxo pipefail
lock() { jq -er --arg t "$1" --arg a "$2" '.tools[$t] as $x | $x.version + " " + ($x.sha256[$a] // $x.sha256.any)' /runner.lock; }
fetch() { # fetch <tool> <lock-arch> <url-template: @V@ is the version> <dest>
  local ver sum
  read -r ver sum < <(lock "$1" "$2")
  mkdir -p "$(dirname "$4")"
  curl -fsSL --retry 3 -o "$4" "${3//@V@/$ver}"
  echo "${sum}  $4" | sha256sum -c -
}
case "$TARGETARCH" in
  amd64) docker_arch=x86_64 runner_arch=x64 ;;
  arm64) docker_arch=aarch64 runner_arch=arm64 ;;
  *) echo "unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;;
esac
fetch docker-cli "$TARGETARCH" "https://download.docker.com/linux/static/stable/${docker_arch}/docker-@V@.tgz" /out/docker-cli/docker.tgz
fetch docker-compose "$TARGETARCH" "https://github.com/docker/compose/releases/download/v@V@/docker-compose-linux-${docker_arch}" /out/docker-compose/docker-compose
fetch actions-runner "$TARGETARCH" "https://github.com/actions/runner/releases/download/v@V@/actions-runner-linux-${runner_arch}-@V@.tar.gz" /out/actions-runner/runner.tgz
fetch semgrep-rules any "https://github.com/semgrep/semgrep-rules/archive/@V@.tar.gz" /out/semgrep-rules/rules.tgz
# Infrastructure tools (fawkes's Terraform, Kubernetes and ArgoCD hooks). Each publisher's own
# checksum file was compared with the pins in runner.lock when they were added. No tfsec: it
# joined Trivy, which the image already has (`trivy config`).
fetch terraform "$TARGETARCH" "https://releases.hashicorp.com/terraform/@V@/terraform_@V@_linux_${TARGETARCH}.zip" /out/terraform/terraform.zip
fetch tflint "$TARGETARCH" "https://github.com/terraform-linters/tflint/releases/download/v@V@/tflint_linux_${TARGETARCH}.zip" /out/tflint/tflint.zip
fetch kubectl "$TARGETARCH" "https://dl.k8s.io/release/v@V@/bin/linux/${TARGETARCH}/kubectl" /out/kubectl/kubectl
fetch helm "$TARGETARCH" "https://get.helm.sh/helm-v@V@-linux-${TARGETARCH}.tar.gz" /out/helm/helm.tgz
fetch kubeconform "$TARGETARCH" "https://github.com/yannh/kubeconform/releases/download/v@V@/kubeconform-linux-${TARGETARCH}.tar.gz" /out/kubeconform/kubeconform.tgz
fetch kustomize "$TARGETARCH" "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv@V@/kustomize_v@V@_linux_${TARGETARCH}.tar.gz" /out/kustomize/kustomize.tgz
fetch argocd "$TARGETARCH" "https://github.com/argoproj/argo-cd/releases/download/v@V@/argocd-linux-${TARGETARCH}" /out/argocd/argocd
SH

FROM base AS final
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]
COPY runner.lock /tmp/runner.lock
COPY python/requirements.lock /tmp/requirements.lock

# semgrep: hash-locked into core's venv (spec R3; same discipline as core's lock).
RUN uv pip install --python /opt/ufawkes/venv/bin/python --require-hashes -r /tmp/requirements.lock \
 && ln -s /opt/ufawkes/venv/bin/semgrep /usr/local/bin/semgrep

# Vendored ruleset, offline (spec §3): the CI-themed directories of the pinned
# semgrep-rules commit. The registry's p/ci pack is defined server-side and
# cannot be rebuilt from the repository, so this approximates it.
RUN --mount=type=bind,from=fetch,source=/out/semgrep-rules,target=/in <<'SH'
set -euxo pipefail
mkdir -p /opt/ufawkes/semgrep-rules
# curl-eval.yaml: its Bash pattern does not parse under the pinned engine (1.179.0),
# and with --error one unparseable rule makes every scan exit 2. Re-test on each bump.
tar -xzf /in/rules.tgz -C /opt/ufawkes/semgrep-rules --strip-components=1 \
  --exclude='*/yaml/github-actions/security/curl-eval.yaml' \
  --wildcards '*/generic/ci' '*/yaml/github-actions' '*/dockerfile' '*/bash'
# -quit, not `| grep -q .`: grep exits at the first match, find can then die of SIGPIPE, and
# pipefail turns that into a build failure that depends on timing.
test -n "$(find /opt/ufawkes/semgrep-rules -name '*.yaml' -print -quit)"
# A clean file must scan to exit 0 offline: catches a ruleset the engine cannot load.
mkdir -p /tmp/clean/.github/workflows
printf 'on: push\njobs:\n  j:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hello\n' > /tmp/clean/.github/workflows/x.yml
semgrep scan --config /opt/ufawkes/semgrep-rules --error --metrics=off --disable-version-check --quiet /tmp/clean
rm -rf /tmp/clean
SH

# Append to core's manifest (an array of {name, version, sha256, variant}); core's
# entries stay untouched (spec R3). The runner and docker tooling are appended in
# the task that installs them.
RUN <<'SH'
set -euxo pipefail
rules="$(jq -r '.tools["semgrep-rules"] | .version + " " + .sha256.any' /tmp/runner.lock)"
sg="$(sha256sum /tmp/requirements.lock | cut -d' ' -f1)"
jq --arg sv "$(semgrep --version)" --arg sg "$sg" --arg rv "${rules% *}" --arg rs "${rules#* }" \
  '. + [{name: "semgrep", version: $sv, sha256: $sg, variant: "ci"}, {name: "semgrep-rules", version: $rv, sha256: $rs, variant: "ci"}]' \
  /etc/ufawkes/tools.json > /etc/ufawkes/tools.json.new
chmod --reference=/etc/ufawkes/tools.json /etc/ufawkes/tools.json.new
mv /etc/ufawkes/tools.json.new /etc/ufawkes/tools.json
SH

# The Actions runner: unpacked from the verified tarball. config.sh and run.sh sit at
# the tarball's root, so .runner and _work land under /opt/ufawkes-runner.
RUN --mount=type=bind,from=fetch,source=/out/actions-runner,target=/in <<'SH'
set -euxo pipefail
mkdir -p /opt/ufawkes-runner /opt/hostedtoolcache
tar -xzf /in/runner.tgz -C /opt/ufawkes-runner
# The .NET runtime's own OS dependencies (ICU, OpenSSL, ...), then drop apt's lists.
apt-get update
/opt/ufawkes-runner/bin/installdependencies.sh
rm -rf /var/lib/apt/lists/*
SH
COPY entrypoints/runner.sh /usr/local/bin/runner.sh

# Trivy's vulnerability DB, baked in so `pipe-ci security` works with no network
# (spec AC2). It is as old as the image: a rebuild refreshes it. Java DB is not baked.
RUN trivy image --download-db-only
COPY entrypoints/pipe-ci /usr/local/bin/pipe-ci

# docker CLI and compose from the verified downloads, then the rest of the manifest.
RUN --mount=type=bind,from=fetch,source=/out,target=/in <<'SH'
set -euxo pipefail
tar -xzf /in/docker-cli/docker.tgz -C /usr/local/bin --strip-components=1 docker/docker
mkdir -p /usr/local/lib/docker/cli-plugins
install -m 0755 /in/docker-compose/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose
jq -c --argjson lock "$(cat /tmp/runner.lock)" --arg arch "$(dpkg --print-architecture)" '
  def entry($n): {name: $n, version: $lock.tools[$n].version, sha256: $lock.tools[$n].sha256[$arch], variant: "ci"};
  . + [entry("actions-runner"), entry("docker-cli"), entry("docker-compose")]' \
  /etc/ufawkes/tools.json > /etc/ufawkes/tools.json.new
chmod --reference=/etc/ufawkes/tools.json /etc/ufawkes/tools.json.new
mv /etc/ufawkes/tools.json.new /etc/ufawkes/tools.json
SH

# The infrastructure tools, from the verified downloads, and their manifest entries.
RUN --mount=type=bind,from=fetch,source=/out,target=/in <<'SH'
set -euxo pipefail
/opt/ufawkes/venv/bin/python -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extract(sys.argv[2], "/usr/local/bin")' /in/terraform/terraform.zip terraform
/opt/ufawkes/venv/bin/python -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extract(sys.argv[2], "/usr/local/bin")' /in/tflint/tflint.zip tflint
install -m 0755 /in/kubectl/kubectl /usr/local/bin/kubectl
install -m 0755 /in/argocd/argocd /usr/local/bin/argocd
tar -xzf /in/helm/helm.tgz -C /usr/local/bin --strip-components=1 "linux-$(dpkg --print-architecture)/helm"
tar -xzf /in/kubeconform/kubeconform.tgz -C /usr/local/bin kubeconform
tar -xzf /in/kustomize/kustomize.tgz -C /usr/local/bin kustomize
chmod 0755 /usr/local/bin/terraform /usr/local/bin/tflint /usr/local/bin/helm /usr/local/bin/kubeconform /usr/local/bin/kustomize
jq -c --argjson lock "$(cat /tmp/runner.lock)" --arg arch "$(dpkg --print-architecture)" '
  def entry($n): {name: $n, version: $lock.tools[$n].version, sha256: $lock.tools[$n].sha256[$arch], variant: "ci"};
  . + [entry("terraform"), entry("tflint"), entry("kubectl"), entry("helm"), entry("kubeconform"), entry("kustomize"), entry("argocd")]' \
  /etc/ufawkes/tools.json > /etc/ufawkes/tools.json.new
chmod --reference=/etc/ufawkes/tools.json /etc/ufawkes/tools.json.new
mv /etc/ufawkes/tools.json.new /etc/ufawkes/tools.json
SH

# The fawkes-core digest this image is built FROM, readable at run time so a caller's
# Pre-flight can check it against the release its devcontainer pins (ci-pipeline R4).
# Read from the FROM line above, so it cannot drift from it.
COPY Dockerfile /tmp/Dockerfile
RUN <<'SH'
set -euxo pipefail
d="$(sed -n 's/^FROM ghcr.io\/paruff\/fawkes-core@\(sha256:[0-9a-f]\{64\}\) AS base$/\1/p' /tmp/Dockerfile)"
test -n "${d}"
printf '%s\n' "${d}" > /etc/ufawkes/ci-base-digest
rm /tmp/Dockerfile
SH

CMD ["bash"]
