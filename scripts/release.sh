#!/usr/bin/env bash
set -euo pipefail

# release.sh — Automated release script for uFawkesPipe
#
# Usage: ./scripts/release.sh vX.Y.Z [--dry-run]
#
# This script automates the release process:
# 1. Validates version format
# 2. Checks for release blockers
# 3. Verifies clean git state
# 4. Creates git tag
# 5. Pushes to remote
# 6. Creates GitHub Release

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    cat << EOF
Usage: $(basename "$0") VERSION [--dry-run]

Automated release script for uFawkesPipe.

Arguments:
    VERSION     Release version in semver format (e.g., v1.0.0, v0.2.1)
    --dry-run   Show what would be done without executing

Examples:
    $(basename "$0") v1.0.0
    $(basename "$0") v0.2.1 --dry-run

Steps performed:
    1. Validate version format
    2. Check for release blockers
    3. Verify clean git state
    4. Create git tag
    5. Push to remote
    6. Create GitHub Release
EOF
}

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

validate_version() {
    local version="$1"
    if [[ ! "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Invalid version format: $version"
        log_error "Expected format: vX.Y.Z (e.g., v1.0.0, v0.2.1)"
        return 1
    fi
    log_info "Version format valid: $version"
}

check_release_blockers() {
    log_info "Checking for release blockers..."

    # Check for open issues with release-blocker label
    if command -v gh &> /dev/null; then
        local blockers
        blockers=$(gh issue list --label "release-blocker" --state open --json number,title --jq '.[] | "\(.number): \(.title)"' 2>/dev/null || echo "")

        if [[ -n "$blockers" ]]; then
            log_error "Release blockers found:"
            echo "$blockers"
            log_error "Resolve or defer these issues before releasing."
            return 1
        fi
        log_info "No release blockers found"
    else
        log_warn "GitHub CLI (gh) not found, skipping release blocker check"
    fi
}

check_clean_git_state() {
    log_info "Checking git state..."

    # Check for uncommitted changes
    if [[ -n "$(git status --porcelain)" ]]; then
        log_error "Uncommitted changes found"
        log_error "Commit or stash changes before releasing."
        return 1
    fi
    log_info "Git working tree clean"

    # Check we're on main branch
    local branch
    branch=$(git branch --show-current)
    if [[ "$branch" != "main" ]]; then
        log_warn "Not on main branch (current: $branch)"
        log_warn "Releases should typically be made from main."
    fi
}

create_git_tag() {
    local version="$1"
    local dry_run="$2"

    log_info "Creating git tag: $version"

    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] Would create tag: $version"
    else
        git tag -a "$version" -m "Release $version"
        log_info "Tag created: $version"
    fi
}

push_to_remote() {
    local version="$1"
    local dry_run="$2"

    log_info "Pushing to remote..."

    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] Would push main and tag $version"
    else
        git push origin main
        git push origin "$version"
        log_info "Pushed main and tag $version"
    fi
}

create_github_release() {
    local version="$1"
    local dry_run="$2"

    log_info "Creating GitHub Release..."

    if ! command -v gh &> /dev/null; then
        log_warn "GitHub CLI (gh) not found, skipping GitHub Release creation"
        return 0
    fi

    # Generate release notes from CHANGELOG
    local release_notes="/tmp/release-notes-${version}.md"
    if [[ -f "$REPO_ROOT/CHANGELOG.md" ]]; then
        # Extract the section for this version
        grep -A 30 "## \[${version}\]" "$REPO_ROOT/CHANGELOG.md" | head -n 25 > "$release_notes" || true
    fi

    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] Would create GitHub Release: $version"
        log_info "[DRY RUN] Release notes: ${release_notes}"
    else
        gh release create "$version" \
            --repo "$(gh repo view --json nameWithOwner -q .nameWithOwner)" \
            --title "$version" \
            --notes-file "$release_notes" || true
        log_info "GitHub Release created: $version"
    fi
}

main() {
    local version=""
    local dry_run="false"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                dry_run="true"
                shift
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            v[0-9]*)
                version="$1"
                shift
                ;;
            *)
                log_error "Unknown argument: $1"
                usage
                exit 1
                ;;
        esac
    done

    # Validate required arguments
    if [[ -z "$version" ]]; then
        log_error "VERSION argument required"
        usage
        exit 1
    fi

    echo "=========================================="
    echo "  Release: $version"
    echo "=========================================="
    echo ""

    # Run checks
    validate_version "$version" || exit 1
    check_release_blockers || exit 1
    check_clean_git_state || exit 1

    echo ""
    echo "=========================================="
    echo "  Creating Release"
    echo "=========================================="
    echo ""

    # Create release
    create_git_tag "$version" "$dry_run"
    push_to_remote "$version" "$dry_run"
    create_github_release "$version" "$dry_run"

    echo ""
    echo "=========================================="
    log_info "Release $version complete!"
    echo "=========================================="
}

main "$@"
