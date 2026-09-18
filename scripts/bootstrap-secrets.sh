#!/usr/bin/env bash
set -euo pipefail

# bootstrap-secrets.sh — Comprehensive secret/bootstrap automation for Woodpecker
#
# Automates token/secret generation across providers and stores in Woodpecker.
#
# Usage:
#   ./scripts/bootstrap-secrets.sh [options]
#
# Options:
#   --woodpecker-host URL         Woodpecker server (default: http://localhost:8000)
#   --woodpecker-admin-token TOKEN  Admin token (or WOODPECKER_ADMIN_TOKEN env)
#   --repo FULL_NAME              Repo (default: paruff/python-fawkes-path)
#
# Provider flags (enable what you need):
#   --sonarqube-url URL           SonarQube base URL
#   --sonarqube-admin USER:PASS   Admin creds
#   --github-org ORG              GitHub org for App/PAT
#   --github-app-id ID            GitHub App ID
#   --github-app-key FILE         GitHub App private key file
#   --gitlab-url URL              GitLab instance URL
#   --gitlab-token TOKEN          GitLab admin token
#   --bitbucket-workspace WS      Bitbucket workspace
#   --bitbucket-user USER         Bitbucket username
#   --bitbucket-app-pass PASS     Bitbucket app password
#   --aws-profile PROFILE         AWS CLI profile
#   --aws-region REGION           AWS region
#   --azure-subscription SUB      Azure subscription ID
#   --azure-rg RG                 Azure resource group
#   --gcp-project PROJECT         GCP project ID
#   --gcp-sa-name NAME            GCP service account name
#
# Secrets to create in Woodpecker (override via env):
#   SONARQUBE_TOKEN, SONARQUBE_URL, SONARQUBE_PROJECT_KEY
#   REGISTRY_USERNAME, REGISTRY_PASSWORD
#   GITHUB_TOKEN, GITLAB_TOKEN, BITBUCKET_TOKEN
#   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
#   AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID
#   GCP_SA_KEY (base64), GCP_PROJECT
#
# Examples:
#   ./scripts/bootstrap-secrets.sh --sonarqube-url http://localhost:9000 --sonarqube-admin admin:admin
#   ./scripts/bootstrap-secrets.sh --github-org myorg --github-app-id 123 --github-app-key app.pem
#   ./scripts/bootstrap-secrets.sh --aws-profile ci-cd --aws-region us-east-1
#   ./scripts/bootstrap-secrets.sh --all-providers

# shellcheck disable=SC2034
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Defaults ────────────────────────────────────────────────────────────────
WOODPECKER_HOST="${WOODPECKER_HOST:-http://localhost:8000}"
REPO_FULL_NAME="${REPO_FULL_NAME:-paruff/python-fawkes-path}"
REPO_VISIBILITY="${REPO_VISIBILITY:-private}"
REPO_TRUSTED="${REPO_TRUSTED:-true}"
WOODPECKER_ADMIN_TOKEN="${WOODPECKER_ADMIN_TOKEN:-}"

# Provider enable flags
ENABLE_SONARQUBE=false
ENABLE_GITHUB=false
ENABLE_GITLAB=false
ENABLE_BITBUCKET=false
ENABLE_AWS=false
ENABLE_AZURE=false
ENABLE_GCP=false

# Provider configs (set via args)
SONARQUBE_URL=""
SONARQUBE_ADMIN_USER=""
SONARQUBE_ADMIN_PASS=""
GITHUB_ORG=""
GITHUB_APP_ID=""
GITHUB_APP_KEY_FILE=""
GITLAB_URL=""
GITLAB_TOKEN=""
BITBUCKET_WORKSPACE=""
BITBUCKET_USER=""
BITBUCKET_APP_PASS=""
AWS_PROFILE=""
AWS_REGION=""
AZURE_SUBSCRIPTION=""
AZURE_RG=""
GCP_PROJECT=""
GCP_SA_NAME=""

# Secret values (generated or from env)
declare -A SECRETS

# ── Helpers ────────────────────────────────────────────────────────────────
log_info() { echo -e "\033[0;32m✓\033[0m $1"; }
log_warn() { echo -e "\033[1;33m⚠\033[0m $1"; }
log_error() { echo -e "\033[0;31m✗\033[0m $1"; }
log_step() { echo -e "\n\033[1;34m▶\033[0m $1"; }

require_cmd() { command -v "$1" >/dev/null 2>&1 || { log_error "$1 not found"; exit 1; }; }
require_env() { [[ -n "${!1}" ]] || { log_error "Required env $1 not set"; exit 1; }; }

api_get() { curl -sf -H "Authorization: Bearer ${WOODPECKER_ADMIN_TOKEN}" "${WOODPECKER_HOST}/api$1"; }
api_post() { curl -sf -X POST -H "Authorization: Bearer ${WOODPECKER_ADMIN_TOKEN}" -H "Content-Type: application/json" -d "$2" "${WOODPECKER_HOST}/api$1"; }
api_patch() { curl -sf -X PATCH -H "Authorization: Bearer ${WOODPECKER_ADMIN_TOKEN}" -H "Content-Type: application/json" -d "$2" "${WOODPECKER_HOST}/api$1"; }

store_secret() {
    local name="$1" value="$2" repo_id="$3"
    existing=$(api_get "/repos/${repo_id}/secrets/${name}" 2>/dev/null || echo "")
    if [[ -n "$existing" && "$existing" != "null" ]]; then
        api_patch "/repos/${repo_id}/secrets/${name}" "$(jq -n --arg v "$value" '{value: $v}')" >/dev/null
        log_info "Updated secret: $name"
    else
        api_post "/repos/${repo_id}/secrets" "$(jq -n --arg n "$name" --arg v "$value" '{name: $n, value: $v, event: "push"}')" >/dev/null
        log_info "Created secret: $name"
    fi
    SECRETS["$name"]="$value"
}

# ── Provider: SonarQube ────────────────────────────────────────────────────
setup_sonarqube() {
    [[ "$ENABLE_SONARQUBE" == true ]] || return 0
    log_step "SonarQube: Generating user token..."

    require_cmd curl jq
    [[ -n "$SONARQUBE_URL" && -n "$SONARQUBE_ADMIN_USER" && -n "$SONARQUBE_ADMIN_PASS" ]] || {
        log_error "SonarQube requires --sonarqube-url and --sonarqube-admin USER:PASS"
        return 1
    }

    local token_name
    token_name="woodpecker-ci-$(date +%s)"
    local response
    response=$(curl -sf -u "${SONARQUBE_ADMIN_USER}:${SONARQUBE_ADMIN_PASS}" \
        -X POST "${SONARQUBE_URL}/api/user_tokens/generate" \
        -d "name=${token_name}" -d "login=woodpecker-ci") || {
        log_error "Failed to generate SonarQube token"
        return 1
    }

    local token
    token=$(echo "$response" | jq -r '.token')
    [[ -n "$token" && "$token" != "null" ]] || { log_error "No token in response"; return 1; }

    SECRETS["SONARQUBE_TOKEN"]="$token"
    SECRETS["SONARQUBE_URL"]="$SONARQUBE_URL"
    log_info "SonarQube token generated"
}

# ── Provider: GitHub (App or PAT) ──────────────────────────────────────────
setup_github() {
    [[ "$ENABLE_GITHUB" == true ]] || return 0
    log_step "GitHub: Generating installation token..."

    require_cmd curl jq openssl
    [[ -n "$GITHUB_APP_ID" && -n "$GITHUB_APP_KEY_FILE" ]] || {
        log_error "GitHub App requires --github-app-id and --github-app-key-file"
        return 1
    }

    # Generate JWT
    local now
    now=$(date +%s)
    local header='{"alg":"RS256","typ":"JWT"}'
    local payload
    payload=$(jq -n --arg iat "$now" --arg exp "$((now + 600))" --arg iss "$GITHUB_APP_ID" \
        '{iat: ($iat|tonumber), exp: ($exp|tonumber), iss: ($iss|tonumber)}')
    local header_b64
    header_b64=$(echo -n "$header" | openssl base64 -e -A | tr '+/' '-_' | tr -d '=')
    local payload_b64
    payload_b64=$(echo -n "$payload" | openssl base64 -e -A | tr '+/' '-_' | tr -d '=')
    local unsigned
    unsigned="${header_b64}.${payload_b64}"
    local signature
    signature=$(echo -n "$unsigned" | openssl dgst -sha256 -sign "$GITHUB_APP_KEY_FILE" | openssl base64 -e -A | tr '+/' '-_' | tr -d '=')
    local jwt
    jwt="${unsigned}.${signature}"

    # Get installation ID
    local installations
    installations=$(curl -sf -H "Authorization: Bearer ${jwt}" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/app/installations") || { log_error "Failed to list installations"; return 1; }

    local installation_id
    if [[ -n "$GITHUB_ORG" ]]; then
        installation_id=$(echo "$installations" | jq -r --arg org "$GITHUB_ORG" '.[] | select(.account.login == $org) | .id')
    else
        installation_id=$(echo "$installations" | jq -r '.[0].id')
    fi
    [[ -n "$installation_id" && "$installation_id" != "null" ]] || { log_error "No installation found for org: $GITHUB_ORG"; return 1; }

    # Get installation token
    local token_resp
    token_resp=$(curl -sf -X POST \
        -H "Authorization: Bearer ${jwt}" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/app/installations/${installation_id}/access_tokens" \
        -d '{"permissions": {"contents": "write", "metadata": "read", "actions": "read", "secrets": "write"}}') || {
        log_error "Failed to get installation token"
        return 1
    }

    local token
    token=$(echo "$token_resp" | jq -r '.token')
    [[ -n "$token" && "$token" != "null" ]] || { log_error "No token in response"; return 1; }

    SECRETS["GITHUB_TOKEN"]="$token"
    log_info "GitHub installation token generated"
}

# ── Provider: GitLab ───────────────────────────────────────────────────────
setup_gitlab() {
    [[ "$ENABLE_GITLAB" == true ]] || return 0
    log_step "GitLab: Using provided token..."

    [[ -n "$GITLAB_URL" && -n "$GITLAB_TOKEN" ]] || {
        log_error "GitLab requires --gitlab-url and --gitlab-token"
        return 1
    }

    GITLAB_TOKEN="${GITLAB_TOKEN}"
    SECRETS["GITLAB_TOKEN"]="$GITLAB_TOKEN"
    SECRETS["GITLAB_URL"]="$GITLAB_URL"
    log_info "GitLab token configured"
}

# ── Provider: Bitbucket ────────────────────────────────────────────────────
setup_bitbucket() {
    [[ "$ENABLE_BITBUCKET" == true ]] || return 0
    log_step "Bitbucket: Using provided app password..."

    [[ -n "$BITBUCKET_WORKSPACE" && -n "$BITBUCKET_USER" && -n "$BITBUCKET_APP_PASS" ]] || {
        log_error "Bitbucket requires --bitbucket-workspace, --bitbucket-user, --bitbucket-app-pass"
        return 1
    }

    SECRETS["BITBUCKET_WORKSPACE"]="$BITBUCKET_WORKSPACE"
    SECRETS["BITBUCKET_USER"]="$BITBUCKET_USER"
    SECRETS["BITBUCKET_APP_PASS"]="$BITBUCKET_APP_PASS"
    log_info "Bitbucket credentials configured"
}

# ── Provider: AWS ──────────────────────────────────────────────────────────
setup_aws() {
    [[ "$ENABLE_AWS" == true ]] || return 0
    log_step "AWS: Creating IAM access keys..."

    require_cmd aws jq
    local profile_opt=""
    [[ -n "$AWS_PROFILE" ]] && profile_opt="--profile $AWS_PROFILE"
    local region_opt=""
    [[ -n "$AWS_REGION" ]] && region_opt="--region $AWS_REGION"

    # Create IAM user if not exists
    local user_name="woodpecker-ci"
    if ! aws iam get-user --user-name "$user_name" $profile_opt $region_opt >/dev/null 2>&1; then
        log_info "Creating IAM user: $user_name"
        aws iam create-user --user-name "$user_name" $profile_opt $region_opt >/dev/null
    fi

    # Attach policies
    local policies=(
        "arn:aws:iam::aws:policy/PowerUserAccess"
    )
    for policy in "${policies[@]}"; do
        aws iam attach-user-policy --user-name "$user_name" --policy-arn "$policy" $profile_opt $region_opt 2>/dev/null || true
    done

    # Create access key
    local key_output
    key_output=$(aws iam create-access-key --user-name "$user_name" $profile_opt $region_opt) || {
        log_error "Failed to create access key"
        return 1
    }

    AWS_ACCESS_KEY_ID=$(echo "$key_output" | jq -r '.AccessKey.AccessKeyId')
    AWS_SECRET_ACCESS_KEY=$(echo "$key_output" | jq -r '.AccessKey.SecretAccessKey')

    SECRETS["AWS_ACCESS_KEY_ID"]="$AWS_ACCESS_KEY_ID"
    SECRETS["AWS_SECRET_ACCESS_KEY"]="$AWS_SECRET_ACCESS_KEY"
    SECRETS["AWS_REGION"]="${AWS_REGION:-us-east-1}"
    log_info "AWS access keys created"
}

# ── Provider: Azure ────────────────────────────────────────────────────────
setup_azure() {
    [[ "$ENABLE_AZURE" == true ]] || return 0
    log_step "Azure: Creating Service Principal..."

    require_cmd az jq
    [[ -n "$AZURE_SUBSCRIPTION" && -n "$AZURE_RG" ]] || {
        log_error "Azure requires --azure-subscription and --azure-rg"
        return 1
    }

    local sp_name
    sp_name="woodpecker-ci-$(date +%s)"
    local sp_output
    sp_output=$(az ad sp create-for-rbac \
        --name "$sp_name" \
        --role contributor \
        --scopes "/subscriptions/${AZURE_SUBSCRIPTION}/resourceGroups/${AZURE_RG}" \
        --sdk-auth) || {
        log_error "Failed to create Azure SP"
        return 1
    }

    local client_id client_secret tenant_id
    client_id=$(echo "$sp_output" | jq -r '.clientId')
    client_secret=$(echo "$sp_output" | jq -r '.clientSecret')
    tenant_id=$(echo "$sp_output" | jq -r '.tenantId')

    SECRETS["AZURE_CLIENT_ID"]="$client_id"
    SECRETS["AZURE_CLIENT_SECRET"]="$client_secret"
    SECRETS["AZURE_TENANT_ID"]="$tenant_id"
    SECRETS["AZURE_SUBSCRIPTION_ID"]="$AZURE_SUBSCRIPTION"
    log_info "Azure Service Principal created"
}

# ── Provider: GCP ──────────────────────────────────────────────────────────
setup_gcp() {
    [[ "$ENABLE_GCP" == true ]] || return 0
    log_step "GCP: Creating Service Account + Key..."

    require_cmd gcloud jq
    [[ -n "$GCP_PROJECT" && -n "$GCP_SA_NAME" ]] || {
        log_error "GCP requires --gcp-project and --gcp-sa-name"
        return 1
    }

    local sa_email="${GCP_SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"

    # Create SA if not exists
    if ! gcloud iam service-accounts describe "$sa_email" --project="$GCP_PROJECT" >/dev/null 2>&1; then
        log_info "Creating service account: $sa_email"
        gcloud iam service-accounts create "$GCP_SA_NAME" \
            --display-name="Woodpecker CI" \
            --project="$GCP_PROJECT" >/dev/null
    fi

    # Grant roles
    local roles=(
        "roles/artifactregistry.writer"
        "roles/run.developer"
        "roles/storage.admin"
    )
    for role in "${roles[@]}"; do
        gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
            --member="serviceAccount:${sa_email}" \
            --role="$role" >/dev/null 2>&1 || true
    done

    # Create key
    local key_file
    key_file="/tmp/gcp-sa-key-$(date +%s).json"
    gcloud iam service-accounts keys create "$key_file" \
        --iam-account="$sa_email" \
        --project="$GCP_PROJECT" >/dev/null

    local sa_key_b64
    sa_key_b64=$(base64 -w 0 < "$key_file")
    rm -f "$key_file"

    SECRETS["GCP_SA_KEY"]="$sa_key_b64"
    SECRETS["GCP_PROJECT"]="$GCP_PROJECT"
    SECRETS["GCP_SA_EMAIL"]="$sa_email"
    log_info "GCP Service Account key created (base64 encoded)"
}

# ── Main Bootstrap ─────────────────────────────────────────────────────────
bootstrap_woodpecker() {
    log_step "Bootstrapping Woodpecker repo..."

    require_cmd curl jq
    require_env WOODPECKER_ADMIN_TOKEN

    # Check server
    if ! curl -sf "${WOODPECKER_HOST}/healthz" >/dev/null; then
        log_error "Woodpecker server not reachable at ${WOODPECKER_HOST}"
        return 1
    fi
    log_info "Server healthy"

    # Get or create repo
    local repo_json
    repo_json=$(api_get "/repos/${REPO_FULL_NAME}" 2>/dev/null || echo "")

    local repo_id
    if [[ -n "$repo_json" && "$repo_json" != "null" ]]; then
        repo_id=$(echo "$repo_json" | jq -r '.id')
        log_info "Repo exists (id: $repo_id)"
    else
        local create_payload
        create_payload=$(jq -n --arg name "$REPO_FULL_NAME" --arg visibility "$REPO_VISIBILITY" --argjson trusted "$REPO_TRUSTED" \
            '{full_name: $name, visibility: $visibility, trusted: $trusted}')
        repo_json=$(api_post "/repos" "$create_payload")
        repo_id=$(echo "$repo_json" | jq -r '.id')
        log_info "Repo created (id: $repo_id)"
    fi

    # Ensure trusted
    local current_trusted
    current_trusted=$(echo "$repo_json" | jq -r '.trusted // false')
    if [[ "$current_trusted" != "true" ]]; then
        api_patch "/repos/${repo_id}" '{"trusted": true}' >/dev/null
        log_info "Trusted mode enabled"
    fi

    # Store all secrets
    for name in "${!SECRETS[@]}"; do
        store_secret "$name" "${SECRETS[$name]}" "$repo_id"
    done

    log_info "All secrets stored in Woodpecker (repo id: $repo_id)"
}

# ── Parse Args ─────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $0 [options]

Comprehensive secret/bootstrap automation for Woodpecker across providers.

Woodpecker:
  --woodpecker-host URL         Woodpecker server (default: http://localhost:8000)
  --woodpecker-admin-token TOKEN  Admin token (or WOODPECKER_ADMIN_TOKEN env)
  --repo FULL_NAME              Repo (default: paruff/python-fawkes-path)

Provider flags (enable what you need):
  --sonarqube-url URL           SonarQube base URL
  --sonarqube-admin USER:PASS   Admin creds
  --github-org ORG              GitHub org for App/PAT
  --github-app-id ID            GitHub App ID
  --github-app-key-file FILE    GitHub App private key file
  --gitlab-url URL              GitLab instance URL
  --gitlab-token TOKEN          GitLab admin token
  --bitbucket-workspace WS      Bitbucket workspace
  --bitbucket-user USER         Bitbucket username
  --bitbucket-app-pass PASS     Bitbucket app password
  --aws-profile PROFILE         AWS CLI profile
  --aws-region REGION           AWS region
  --azure-subscription SUB      Azure subscription ID
  --azure-rg RG                 Azure resource group
  --gcp-project PROJECT         GCP project ID
  --gcp-sa-name NAME            GCP service account name

Shortcuts:
  --all-providers               Enable all providers

Secret overrides (or set via env):
  SONARQUBE_TOKEN, SONARQUBE_URL, SONARQUBE_PROJECT_KEY
  REGISTRY_USERNAME, REGISTRY_PASSWORD
  GITHUB_TOKEN, GITLAB_TOKEN, BITBUCKET_TOKEN
  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
  AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID
  GCP_SA_KEY (base64), GCP_PROJECT

Examples:
  $0 --sonarqube-url http://localhost:9000 --sonarqube-admin admin:admin
  $0 --github-org myorg --github-app-id 123 --github-app-key-file app.pem
  $0 --aws-profile ci-cd --aws-region us-east-1
  $0 --all-providers

EOF
    exit 0
}

parse_args() {
    while (( $# > 0 )); do
        case "$1" in
            --help|-h) usage ;;
            --woodpecker-host) WOODPECKER_HOST="$2"; shift 2 ;;
            --woodpecker-admin-token) WOODPECKER_ADMIN_TOKEN="$2"; shift 2 ;;
            --repo) REPO_FULL_NAME="$2"; shift 2 ;;
            --sonarqube-url) SONARQUBE_URL="$2"; ENABLE_SONARQUBE=true; shift 2 ;;
            --sonarqube-admin) SONARQUBE_ADMIN_USER="${2%:*}"; SONARQUBE_ADMIN_PASS="${2#*:}"; ENABLE_SONARQUBE=true; shift 2 ;;
            --github-org) GITHUB_ORG="$2"; ENABLE_GITHUB=true; shift 2 ;;
            --github-app-id) GITHUB_APP_ID="$2"; ENABLE_GITHUB=true; shift 2 ;;
            --github-app-key-file) GITHUB_APP_KEY_FILE="$2"; shift 2 ;;
            --gitlab-url) GITLAB_URL="$2"; ENABLE_GITLAB=true; shift 2 ;;
            --gitlab-token) GITLAB_TOKEN="$2"; ENABLE_GITLAB=true; shift 2 ;;
            --bitbucket-workspace) BITBUCKET_WORKSPACE="$2"; ENABLE_BITBUCKET=true; shift 2 ;;
            --bitbucket-user) BITBUCKET_USER="$2"; shift 2 ;;
            --bitbucket-app-pass) BITBUCKET_APP_PASS="$2"; ENABLE_BITBUCKET=true; shift 2 ;;
            --aws-profile) AWS_PROFILE="$2"; ENABLE_AWS=true; shift 2 ;;
            --aws-region) AWS_REGION="$2"; shift 2 ;;
            --azure-subscription) AZURE_SUBSCRIPTION="$2"; ENABLE_AZURE=true; shift 2 ;;
            --azure-rg) AZURE_RG="$2"; shift 2 ;;
            --gcp-project) GCP_PROJECT="$2"; ENABLE_GCP=true; shift 2 ;;
            --gcp-sa-name) GCP_SA_NAME="$2"; shift 2 ;;
            --all-providers)
                ENABLE_SONARQUBE=true
                ENABLE_GITHUB=true
                ENABLE_GITLAB=true
                ENABLE_BITBUCKET=true
                ENABLE_AWS=true
                ENABLE_AZURE=true
                ENABLE_GCP=true
                shift ;;
            *) log_error "Unknown option: $1"; exit 1 ;;
        esac
    done

    # Load env defaults for secrets
    SECRETS["SONARQUBE_URL"]="${SONARQUBE_URL:-http://sonarqube:9000}"
    SECRETS["SONARQUBE_PROJECT_KEY"]="${SONARQUBE_PROJECT_KEY:-python-fawkes-path}"
    SECRETS["REGISTRY_USERNAME"]="${REGISTRY_USERNAME:-test}"
    SECRETS["REGISTRY_PASSWORD"]="${REGISTRY_PASSWORD:-test}"
}

# ── Main ───────────────────────────────────────────────────────────────────
main() {
    # Handle --help early
    for arg in "$@"; do
        [[ "$arg" == "--help" || "$arg" == "-h" ]] && usage
    done

    echo "=========================================="
    echo "  Comprehensive Secrets Bootstrap"
    echo "=========================================="
    echo "Host: $WOODPECKER_HOST"
    echo "Repo: $REPO_FULL_NAME"
    echo ""

    parse_args "$@"

    require_env WOODPECKER_ADMIN_TOKEN

    # Setup enabled providers
    setup_sonarqube
    setup_github
    setup_gitlab
    setup_bitbucket
    setup_aws
    setup_azure
    setup_gcp

    # Bootstrap Woodpecker
    bootstrap_woodpecker

    echo ""
    echo "=========================================="
    log_info "Bootstrap complete!"
    echo "=========================================="
    echo "Configured secrets:"
    for name in "${!SECRETS[@]}"; do
        echo "  $name: (stored — value not printed)"
    done
    echo ""
    echo "Next: Push to trigger pipeline → watch at ${WOODPECKER_HOST}/repos/${REPO_FULL_NAME}"
}

main "$@"
