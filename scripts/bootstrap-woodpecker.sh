#!/usr/bin/env bash
set -euo pipefail

# bootstrap-woodpecker.sh — Idempotent Woodpecker repo + secrets bootstrap
#
# Usage:
#   make bootstrap-woodpecker
#   ./scripts/bootstrap-woodpecker.sh
#
# Requires: Woodpecker server running at WOODPECKER_HOST (default: http://localhost:8000)
#           Admin token in WOODPECKER_ADMIN_TOKEN env var or Woodpecker admin UI

# shellcheck disable=SC2034
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Config (override via env) ──────────────────────────────────────────────
WOODPECKER_HOST="${WOODPECKER_HOST:-http://localhost:8000}"
REPO_FULL_NAME="${REPO_FULL_NAME:-paruff/python-fawkes-path}"
REPO_VISIBILITY="${REPO_VISIBILITY:-private}"
REPO_TRUSTED="${REPO_TRUSTED:-true}"

# Default test secrets (override via env)
SONARQUBE_TOKEN="${SONARQUBE_TOKEN:-test-sonarqube-token}"
SONARQUBE_URL="${SONARQUBE_URL:-http://sonarqube:9000}"
SONARQUBE_PROJECT_KEY="${SONARQUBE_PROJECT_KEY:-python-fawkes-path}"
REGISTRY_USERNAME="${REGISTRY_USERNAME:-test}"
REGISTRY_PASSWORD="${REGISTRY_PASSWORD:-test}"

# Admin token (required for API calls)
# Get from: Woodpecker UI → Admin → API → Generate Token
WOODPECKER_ADMIN_TOKEN="${WOODPECKER_ADMIN_TOKEN:-}"

# ── Helpers ────────────────────────────────────────────────────────────────
log_info() { echo -e "\033[0;32m✓\033[0m $1"; }
log_warn() { echo -e "\033[1;33m⚠\033[0m $1"; }
log_error() { echo -e "\033[0;31m✗\033[0m $1"; }

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || { log_error "$1 not found in PATH"; exit 1; }
}

require_env() {
    if [[ -z "${!1}" ]]; then
        log_error "Required environment variable $1 not set"
        exit 1
    fi
}

api_get() {
    curl -sf -H "Authorization: Bearer ${WOODPECKER_ADMIN_TOKEN}" \
         "${WOODPECKER_HOST}/api$1"
}

api_post() {
    curl -sf -X POST -H "Authorization: Bearer ${WOODPECKER_ADMIN_TOKEN}" \
         -H "Content-Type: application/json" \
         -d "$2" "${WOODPECKER_HOST}/api$1"
}

api_patch() {
    curl -sf -X PATCH -H "Authorization: Bearer ${WOODPECKER_ADMIN_TOKEN}" \
         -H "Content-Type: application/json" \
         -d "$2" "${WOODPECKER_HOST}/api$1"
}

# ── Main ───────────────────────────────────────────────────────────────────
main() {
    echo "=========================================="
    echo "  Woodpecker Bootstrap"
    echo "=========================================="
    echo "Host: $WOODPECKER_HOST"
    echo "Repo: $REPO_FULL_NAME"
    echo ""

    require_cmd curl
    require_env WOODPECKER_ADMIN_TOKEN

    # 1. Check server health
    log_info "Checking Woodpecker server..."
    if ! curl -sf "${WOODPECKER_HOST}/healthz" >/dev/null; then
        log_error "Woodpecker server not reachable at ${WOODPECKER_HOST}"
        exit 1
    fi
    log_info "Server healthy"

    # 2. Check if repo exists
    log_info "Checking repo: ${REPO_FULL_NAME}"
    repo_json=$(api_get "/repos/${REPO_FULL_NAME}" 2>/dev/null || echo "")

    if [[ -n "$repo_json" && "$repo_json" != "null" ]]; then
        repo_id=$(echo "$repo_json" | jq -r '.id')
        log_info "Repo exists (id: $repo_id)"
    else
        # Create repo
        log_info "Creating repo: ${REPO_FULL_NAME}"
        create_payload=$(jq -n \
            --arg name "$REPO_FULL_NAME" \
            --arg visibility "$REPO_VISIBILITY" \
            --argjson trusted "$REPO_TRUSTED" \
            '{full_name: $name, visibility: $visibility, trusted: $trusted}')
        repo_json=$(api_post "/repos" "$create_payload")
        repo_id=$(echo "$repo_json" | jq -r '.id')
        log_info "Repo created (id: $repo_id)"
    fi

    # 3. Update repo to ensure trusted=true
    current_trusted=$(echo "$repo_json" | jq -r '.trusted // false')
    if [[ "$current_trusted" != "true" ]]; then
        log_info "Enabling trusted mode"
        api_patch "/repos/${repo_id}" '{"trusted": true}' >/dev/null
        log_info "Trusted mode enabled"
    fi

    # 4. Add/update secrets
    declare -A secrets=(
        ["SONARQUBE_TOKEN"]="$SONARQUBE_TOKEN"
        ["SONARQUBE_URL"]="$SONARQUBE_URL"
        ["SONARQUBE_PROJECT_KEY"]="$SONARQUBE_PROJECT_KEY"
        ["REGISTRY_USERNAME"]="$REGISTRY_USERNAME"
        ["REGISTRY_PASSWORD"]="$REGISTRY_PASSWORD"
    )

    log_info "Configuring secrets..."
    for name in "${!secrets[@]}"; do
        value="${secrets[$name]}"
        # Check if secret exists
        existing=$(api_get "/repos/${repo_id}/secrets/${name}" 2>/dev/null || echo "")

        if [[ -n "$existing" && "$existing" != "null" ]]; then
            # Update
            api_patch "/repos/${repo_id}/secrets/${name}" \
                "$(jq -n --arg v "$value" '{value: $v}')" >/dev/null
            log_info "Updated secret: $name"
        else
            # Create
            api_post "/repos/${repo_id}/secrets" \
                "$(jq -n --arg n "$name" --arg v "$value" '{name: $n, value: $v, event: "push"}')" >/dev/null
            log_info "Created secret: $name"
        fi
    done

    # 5. Verify repo accessible
    log_info "Verifying repo configuration..."
    verify=$(api_get "/repos/${repo_id}")
    if [[ -n "$verify" && "$verify" != "null" ]]; then
        log_info "Repo verified: $(echo "$verify" | jq -r '.full_name')"
    fi

    echo ""
    echo "=========================================="
    log_info "Bootstrap complete!"
    echo "=========================================="
    echo "Repo: ${REPO_FULL_NAME} (id: ${repo_id})"
    echo "Trusted: true"
    echo "Secrets configured: ${#secrets[@]}"
    echo ""
    echo "Next steps:"
    echo "  1. Push to repo to trigger pipeline: git push origin main"
    echo "  2. Watch pipeline at: ${WOODPECKER_HOST}/repos/${REPO_FULL_NAME}"
    echo "  3. For real tokens, set env vars before running:"
    echo "     export SONARQUBE_TOKEN=your-real-token"
    echo "     export REGISTRY_USERNAME=your-registry-user"
    echo "     export REGISTRY_PASSWORD=your-registry-password"
    echo "     ./scripts/bootstrap-woodpecker.sh"
}

main "$@"
