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
find /opt/ufawkes/semgrep-rules -name '*.yaml' | grep -q .
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
