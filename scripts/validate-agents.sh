#!/bin/bash
# Validate agent and skill definitions for consistency and completeness.
# Run: ./scripts/validate-agents.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

errors=0
warnings=0

echo "========================================="
echo "Agent & Skill Validation"
echo "========================================="
echo ""

# 1. Check all applies: paths exist
echo "🔍 Checking applies: frontmatter paths..."
for f in .agents/agents/*.md .agents/skills/*.md; do
    if [ ! -f "$f" ]; then
        continue
    fi
    # Extract applies: value from YAML frontmatter
    applies=$(sed -n '/^---$/,/^---$/p' "$f" | grep "^applies:" | sed 's/applies: *//' || true)
    if [ -n "$applies" ] && [ "$applies" != "**/*" ]; then
        # Check if any files match the pattern (simplified check)
        has_files=false
        IFS=',' read -ra PATTERNS <<< "$applies"
        for pattern in "${PATTERNS[@]}"; do
            pattern=$(echo "$pattern" | xargs)  # trim whitespace
            # Simple glob check
            if ls $pattern >/dev/null 2>&1; then
                has_files=true
                break
            fi
        done
        if [ "$has_files" = false ]; then
            echo -e "${YELLOW}⚠️  $f: applies: '$applies' matches no files${NC}"
            warnings=$((warnings + 1))
        else
            echo -e "${GREEN}✅ $f: applies: '$applies' matches files${NC}"
        fi
    else
        echo -e "${GREEN}✅ $f: applies: wildcard (OK)${NC}"
    fi
done

echo ""

# 2. Check all context file references exist
echo "🔍 Checking context file references..."
for f in .agents/agents/*.md .agents/skills/*.md; do
    if [ ! -f "$f" ]; then
        continue
    fi
    # Find lines with file references (backtick-quoted paths)
    refs=$(grep -o '`[a-zA-Z_/.-]*\.[a-zA-Z]*`' "$f" | tr -d '`' || true)
    for ref in $refs; do
        if [ ! -f "$ref" ] && [ ! -d "$ref" ]; then
            echo -e "${YELLOW}⚠️  $f references '$ref' which does not exist${NC}"
            warnings=$((warnings + 1))
        fi
    done
done

echo ""

# 3. Check DORA format consistency
echo "🔍 Checking DORA format consistency..."
dora_source=".agents/specs/dora-log-format.md"
if [ ! -f "$dora_source" ]; then
    echo -e "${RED}❌ Missing DORA format spec: $dora_source${NC}"
    errors=$((errors + 1))
else
    # Check that agents reference the spec or use consistent format
    for f in .agents/agents/*.md .agents/skills/*.md; do
        if [ ! -f "$f" ]; then
            continue
        fi
        # Check for inconsistent DORA formats (space-delimited without prefix)
        if grep -q "stage-start:.*step:" "$f" 2>/dev/null; then
            echo -e "${RED}❌ $f: Uses space-delimited DORA format (should use colon-delimited with dora: prefix)${NC}"
            errors=$((errors + 1))
        # Check for missing dora: prefix (look for lines with dora: prefix but NOT lines with dora: prefix followed by stage)
        elif grep -qE "^stage-start:" "$f" 2>/dev/null; then
            echo -e "${RED}❌ $f: Missing 'dora:' prefix in DORA log format${NC}"
            errors=$((errors + 1))
        # Check for ISO timestamps instead of isoNow()
        elif grep -qE "stage-start:.*[0-9]{4}-[0-9]{2}-[0-9]{2}T" "$f" 2>/dev/null; then
            echo -e "${RED}❌ $f: Uses hardcoded ISO timestamp (should use isoNow())${NC}"
            errors=$((errors + 1))
        fi
    done
    echo -e "${GREEN}✅ DORA format spec exists${NC}"
fi

echo ""

# 4. Check for credential patterns in agent files
echo "🔍 Checking for credential patterns..."
credential_found=false
for f in .agents/agents/*.md .agents/skills/*.md; do
    if [ ! -f "$f" ]; then
        continue
    fi
    if grep -qiE '(password|secret|token|api.key)\s*[:=]\s*["\x27][^"\x27]{8,}' "$f" 2>/dev/null; then
        echo -e "${RED}❌ $f: Potential credential found${NC}"
        errors=$((errors + 1))
        credential_found=true
    fi
done
if [ "$credential_found" = false ]; then
    echo -e "${GREEN}✅ No credentials found in agent/skill files${NC}"
fi

echo ""

# 5. Check agent registry matches actual files
echo "🔍 Checking agent registry completeness..."
agent_files=$(ls .agents/agents/*.md 2>/dev/null | wc -l)
skill_files=$(ls .agents/skills/*.md 2>/dev/null | wc -l)
spec_files=$(ls .agents/specs/*.md 2>/dev/null | wc -l)
echo -e "${GREEN}✅ Found $agent_files agents, $skill_files skills, $spec_files specs${NC}"

echo ""

# 6. Check for overlapping agents
echo "🔍 Checking for agent/skill overlap..."
buildpack_desc=$(grep "^description:" .agents/agents/buildpack-agent.md 2>/dev/null | head -1 || true)
langpack_desc=$(grep "^description:" .agents/skills/language-pack.md 2>/dev/null | head -1 || true)
if [ -n "$buildpack_desc" ] && [ -n "$langpack_desc" ]; then
    echo -e "${YELLOW}⚠️  buildpack-agent and language-pack may overlap — verify descriptions are distinct${NC}"
    warnings=$((warnings + 1))
fi

echo ""

# Summary
echo "========================================="
if [ "$errors" -gt 0 ]; then
    echo -e "${RED}❌ Validation failed with $errors error(s), $warnings warning(s)${NC}"
    exit 1
elif [ "$warnings" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Validation passed with $warnings warning(s)${NC}"
else
    echo -e "${GREEN}✅ All agent/skill validations passed${NC}"
fi
echo "========================================="
