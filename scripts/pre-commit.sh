#!/bin/bash
# Pre-commit hook for uFawkesPipe
# Checks: lint, secrets, security, and legacy deliveryd references

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

errors=0

echo "========================================="
echo "uFawkesPipe Pre-Commit Checks"
echo "========================================="

# 1. ShellCheck
echo ""
echo "🔍 Running ShellCheck..."
if command -v shellcheck &> /dev/null; then
    shell_files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(sh|bash)$' || true)
    if [ -n "$shell_files" ]; then
        for f in $shell_files; do
            if [ -f "$f" ] && ! shellcheck -S warning "$f" 2>/dev/null; then
                echo -e "${RED}❌ ShellCheck failed: $f${NC}"
                errors=$((errors + 1))
            fi
        done
    fi
    # Also check validate.sh always
    if [ -f "validate.sh" ] && ! shellcheck -S warning validate.sh 2>/dev/null; then
        echo -e "${RED}❌ ShellCheck failed: validate.sh${NC}"
        errors=$((errors + 1))
    fi
    echo -e "${GREEN}✅ ShellCheck passed${NC}"
else
    echo -e "${YELLOW}⚠️  shellcheck not installed, skipping${NC}"
fi

# 2. YAML lint
echo ""
echo "🔍 Checking YAML files..."
if command -v yamllint &> /dev/null; then
    yaml_files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ya?ml)$' || true)
    if [ -n "$yaml_files" ]; then
        for f in $yaml_files; do
            if [ -f "$f" ] && ! yamllint -d '{extends: default, rules: {line-length: disable, document-start: disable, truthy: disable, indentation: {spaces: 2, indent-sequences: whatever}}}' "$f" 2>/dev/null; then
                echo -e "${RED}❌ yamllint failed: $f${NC}"
                errors=$((errors + 1))
            fi
        done
    fi
    echo -e "${GREEN}✅ YAML lint passed${NC}"
else
    echo -e "${YELLOW}⚠️  yamllint not installed, skipping${NC}"
fi

# 3. Secret detection
echo ""
echo "🔍 Scanning for secrets..."
staged_files=$(git diff --cached --name-only --diff-filter=ACM || true)
secret_patterns=(
    'AKIA[0-9A-Z]{16}'           # AWS Access Key
    'ghp_[A-Za-z0-9]{36}'        # GitHub Personal Access Token
    'sk-[A-Za-z0-9]{32,}'        # OpenAI API key
    'xox[bpsa]-[A-Za-z0-9-]+'    # Slack token
)

for file in $staged_files; do
    if [ -f "$file" ] && [[ ! "$file" =~ \.(png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$ ]]; then
        for pattern in "${secret_patterns[@]}"; do
            if grep -qE "$pattern" "$file" 2>/dev/null; then
                echo -e "${RED}❌ Potential secret in $file (pattern: ${pattern:0:20}...)${NC}"
                errors=$((errors + 1))
            fi
        done
    fi
done
echo -e "${GREEN}✅ Secret scan passed${NC}"

# 4. Check .env files not staged
echo ""
echo "🔍 Checking for .env files..."
env_files=$(git diff --cached --name-only | grep -E '\.env$|\.env\.' | grep -v '\.env\.example$' || true)
if [ -n "$env_files" ]; then
    echo -e "${RED}❌ The following .env files should not be committed:${NC}"
    echo "$env_files"
    errors=$((errors + 1))
else
    echo -e "${GREEN}✅ No .env files staged${NC}"
fi

# 5. Deliveryd reference check (Phase D)
echo ""
echo "🔍 Checking for leftover 'deliveryd' references..."
deliveryd_refs=$(git diff --cached --name-only --diff-filter=ACM | xargs grep -l "deliveryd" 2>/dev/null | grep -v ".deliveryd.yml" | grep -v ".git/" | grep -v ".agents/" || true)
if [ -n "$deliveryd_refs" ]; then
    echo -e "${YELLOW}⚠️  Found 'deliveryd' references in:${NC}"
    echo "$deliveryd_refs"
    echo -e "${YELLOW}   This is expected during Phase D migration (deprecation shim).${NC}"
    echo -e "${YELLOW}   After migration complete, these should be removed.${NC}"
fi

# 6. Docker Compose validation (compose.yaml — current stack)
echo ""
echo "🔍 Validating compose.yaml..."
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    if docker compose -f compose.yaml config > /dev/null 2>&1; then
        echo -e "${GREEN}✅ compose.yaml is valid${NC}"
    else
        echo -e "${RED}❌ compose.yaml has errors${NC}"
        errors=$((errors + 1))
    fi
else
    echo -e "${YELLOW}⚠️  Docker Compose not available, skipping${NC}"
fi

# 7. No 'latest' image tags in compose
echo ""
echo "🔍 Checking for 'latest' image tags..."
if [ -f "compose.yaml" ]; then
    latest_tags=$(grep -n "image:.*:latest" compose.yaml | grep -v "^\s*#" | grep -v "^.*#" || true)
    if [ -n "$latest_tags" ]; then
        echo -e "${RED}❌ Found 'latest' image tags in compose.yaml:${NC}"
        echo "$latest_tags"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ No 'latest' image tags${NC}"
    fi
fi

# 8. Agent/skill validation
echo ""
echo "🔍 Validating agent and skill definitions..."
if [ -f "scripts/validate-agents.sh" ]; then
    if ./scripts/validate-agents.sh 2>/dev/null; then
        echo -e "${GREEN}✅ Agent/skill validation passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Agent/skill validation had warnings (non-blocking)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  scripts/validate-agents.sh not found, skipping${NC}"
fi

# Summary
echo ""
echo "========================================="
if [ "$errors" -gt 0 ]; then
    echo -e "${RED}❌ Pre-commit failed with $errors error(s)${NC}"
    echo "Fix the issues above and try again."
    exit 1
else
    echo -e "${GREEN}✅ All pre-commit checks passed${NC}"
fi
echo "========================================="
