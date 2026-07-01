#!/usr/bin/env bash
# uFawkesPipe Shared DORA Logging Utility
#
# Source this script in pipeline steps to emit structured JSON logs
# compatible with uFawkesObs/Loki ingestion via Alloy.
#
# Usage:
#   source /drone/src/scripts/dora-log.sh
#   dora_start "my-step"
#   dora_info "my-step" "Processing item 1 of 5"
#   dora_warn "my-step" "Non-critical issue detected"
#   # ... do work ...
#   dora_end "my-step"
#
# Or for error conditions:
#   dora_error "my-step" "Critical failure: connection refused" ',"exit_code":1'
#   exit 1
#
# Each function emits one JSON line to stdout with:
#   @timestamp, level, logger, message, pipeline, repo, step
#
# Optional extra_fields can be appended as a raw JSON fragment
# (e.g. ',"exit_code":1,"secrets_found":true').

set -euo pipefail

dora_emit() {
  local level="$1"
  local logger="$2"
  local message="$3"
  local extra_fields="${4:-}"

  # shellcheck disable=SC2086
  printf '{"@timestamp":"%s","level":"%s","logger":"%s","message":"%s","pipeline":"%s","repo":"%s","step":"%s"%s}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "${level}" \
    "${logger}" \
    "${message}" \
    "${CI_PIPELINE_NUMBER:-unknown}" \
    "${CI_REPO:-unknown}" \
    "${CI_STEP_NAME:-unknown}" \
    "${extra_fields}"
}

dora_start() {
  dora_emit "info" "$1" "Starting ${1}"
}

dora_end() {
  dora_emit "info" "$1" "Completed ${1}"
}

dora_info() {
  local logger="$1"
  local message="$2"
  dora_emit "info" "${logger}" "${message}"
}

dora_warn() {
  local logger="$1"
  local message="$2"
  local extra_fields="${3:-}"
  dora_emit "warn" "${logger}" "${message}" "${extra_fields}"
}

dora_error() {
  local logger="$1"
  local message="$2"
  local extra_fields="${3:-}"
  dora_emit "error" "${logger}" "${message}" "${extra_fields}"
}
