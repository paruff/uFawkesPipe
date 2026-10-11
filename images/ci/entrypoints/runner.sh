#!/usr/bin/env bash
# runner.sh — dispatch-only self-hosted runner mode of ufawkes-ci (spec R4, R8).
# Registers the runner once, then execs it. Every failure is loud: a runner that
# could not register must never look like one that is running.
#
# Required env: RUNNER_REPO_URL, RUNNER_TOKEN, RUNNER_NAME
# Optional env: RUNNER_EXTRA_LABELS (comma separated, added to self-hosted,pipe-ci)
#
# Exit codes: 2 missing required env (names the variable), 3 registration failed
# (prints config.sh's log).
set -euo pipefail

RUNNER_HOME=/opt/ufawkes-runner

for var in RUNNER_REPO_URL RUNNER_TOKEN RUNNER_NAME; do
  if [[ -z "${!var:-}" ]]; then
    echo "runner.sh: missing required env: ${var}" >&2
    exit 2
  fi
done

# The container runs as root on purpose (spec §4); the runner needs to be told so.
export RUNNER_ALLOW_RUNASROOT=1

if [[ ! -f "${RUNNER_HOME}/.runner" ]]; then
  log="$(mktemp)"
  if ! "${RUNNER_HOME}/config.sh" \
    --url "${RUNNER_REPO_URL}" \
    --token "${RUNNER_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --labels "self-hosted,pipe-ci${RUNNER_EXTRA_LABELS:+,${RUNNER_EXTRA_LABELS}}" \
    --unattended --replace \
    --work "${RUNNER_HOME}/_work" > "${log}" 2>&1; then
    cat "${log}" >&2
    echo "runner.sh: runner registration failed (config.sh above)" >&2
    exit 3
  fi
fi

export RUNNER_TOOL_CACHE=/opt/hostedtoolcache
exec "${RUNNER_HOME}/run.sh"
