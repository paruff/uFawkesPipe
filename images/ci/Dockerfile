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

# Task 5 assembles the final image from /out; until then, building it proves the verify stage.
FROM base AS final
COPY --from=fetch /out /opt/ufawkes-ci/verified
