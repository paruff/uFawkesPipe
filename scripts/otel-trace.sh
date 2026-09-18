#!/usr/bin/env bash
# uFawkesPipe OTEL Trace Wrapper (P3-4)
#
# Woodpecker CE has no native per-step OTEL span emission ("Woodpecker
# native or wrapper" per EXECUTION_QUEUE.md P3-4) — this is the wrapper.
# It builds a minimal OTLP/HTTP JSON span per step and POSTs it directly
# to the collector, sharing one trace_id across every step in a pipeline
# run so Tempo/Grafana render them as one trace with sibling spans.
#
# Usage:
#   source /drone/src/scripts/otel-trace.sh
#   otel_span_start "sast"
#   # ... do work ...
#   otel_span_end "sast"          # status: ok
#   otel_span_end "sast" "error"  # status: error
#
# ponytail: only wired into steps whose image has both curl and a shell
# (sast/sonar-scanner-cli, dast/zap-stable, defectdojo-upload/curlimages).
# docker:24-cli, aquasec/trivy and ghcr.io/google/osv-scanner have neither
# curl nor wget-with-POST — confirmed while building this — so lint/test/
# build/image-scan/dependency-scan/push/deploy steps get no span in this
# iteration. Upgrade path: add curl to those images (a custom wrapper
# image, or `apk add curl` as the step's first command) once full-pipeline
# tracing is needed; this script already no-ops safely if curl is missing.
#
# trace_id/span_id are derived deterministically from CI_REPO_NAME/
# CI_PIPELINE_NUMBER/CI_STEP_NAME via cksum (POSIX, present in every image
# this repo's generator uses — sha256sum/md5sum are not), not a real
# random/crypto generator. Collision risk is negligible for one trace per
# pipeline run but not zero.
#
# Requires: OTEL_EXPORTER_OTLP_ENDPOINT in its gRPC form (e.g.
# http://otel-collector:4317, as already set in compose.suite.yaml) — the
# :4317 is swapped for :4318 (OTLP/HTTP) since this wrapper speaks
# OTLP/HTTP JSON, not gRPC/protobuf. Silently no-ops (never fails the
# build) if that var is unset, or if curl isn't on PATH.

set -uo pipefail  # deliberately no -e: tracing must never fail the pipeline

_otel_hex16() {
  # 64-bit deterministic hex id from a string.
  printf '%016x' "$(echo -n "$1" | cksum | cut -d' ' -f1)"
}

_otel_trace_id() {
  # 128 bits: two independently-seeded hex16 halves.
  printf '%s%s' \
    "$(_otel_hex16 "${CI_REPO_NAME:-unknown}-${CI_PIPELINE_NUMBER:-0}")" \
    "$(_otel_hex16 "${CI_PIPELINE_NUMBER:-0}-${CI_REPO_NAME:-unknown}")"
}

_otel_http_endpoint() {
  local ep="${OTEL_EXPORTER_OTLP_ENDPOINT:-}"
  [[ -z "$ep" ]] && return 1
  echo "${ep/:4317/:4318}"
}

_otel_now_ns() {
  local raw
  raw=$(date +%s%N 2>/dev/null || echo "")
  if [[ "$raw" =~ ^[0-9]+$ ]] && (( ${#raw} > 10 )); then
    echo "$raw"
  else
    # busybox `date` silently drops %N — fall back to second precision.
    echo "$(date +%s)000000000"
  fi
}

otel_span_start() {
  local name="$1"
  export _OTEL_SPAN_ID
  _OTEL_SPAN_ID=$(_otel_hex16 "${CI_PIPELINE_NUMBER:-0}-${CI_REPO_NAME:-unknown}-${name}")
  export _OTEL_START_NS
  _OTEL_START_NS=$(_otel_now_ns)
}

otel_span_end() {
  local name="$1"
  local status="${2:-ok}"

  command -v curl >/dev/null 2>&1 || return 0
  local endpoint
  endpoint=$(_otel_http_endpoint) || return 0

  local end_ns
  end_ns=$(_otel_now_ns)
  local trace_id
  trace_id=$(_otel_trace_id)
  local span_id="${_OTEL_SPAN_ID:-$(_otel_hex16 "$name")}"
  local status_code=1 # OTLP StatusCode: 1=Ok, 2=Error
  [[ "$status" == "error" ]] && status_code=2

  local payload
  payload=$(printf '{"resourceSpans":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"%s"}}]},"scopeSpans":[{"spans":[{"traceId":"%s","spanId":"%s","name":"%s","kind":1,"startTimeUnixNano":"%s","endTimeUnixNano":"%s","status":{"code":%s}}]}]}]}' \
    "${CI_REPO_NAME:-unknown}" "${trace_id}" "${span_id}" "${name}" \
    "${_OTEL_START_NS:-${end_ns}}" "${end_ns}" "${status_code}")

  curl -sf -m 5 -X POST "${endpoint}/v1/traces" \
    -H "Content-Type: application/json" -d "${payload}" >/dev/null 2>&1 || true
}
