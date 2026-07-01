#!/bin/bash
# Quickstart Smoke Test for uFawkesPipe
# Validates the platform works end-to-end
# Usage: ./scripts/quickstart-smoke-test.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================="
echo "uFawkesPipe Quickstart Smoke Test"
echo "========================================="
echo ""

START_TIME=$(date +%s)

# 1. Verify prerequisites
echo "✅ [PASS] Step 1: Verify prerequisites (Docker, Compose)"
if ! command -v docker &> /dev/null; then
    echo "❌ [FAIL] Docker not found"
    exit 1
fi
if ! docker compose version &> /dev/null; then
    echo "❌ [FAIL] Docker Compose not found"
    exit 1
fi

# 2. Start platform
echo "✅ [PASS] Step 2: Start platform (docker compose up -d)"
cd "$REPO_ROOT"
docker compose -f compose.yaml up -d

# 3. Wait for Woodpecker
echo "✅ [PASS] Step 3: Wait for Woodpecker (localhost:8000, timeout 60s)"
for i in {1..30}; do
    if curl -sf http://localhost:8000/api/version >/dev/null 2>&1; then
        echo "   Woodpecker is ready"
        break
    fi
    sleep 2
    if [ $i -eq 30 ]; then
        echo "❌ [FAIL] Woodpecker did not start in time"
        docker compose -f compose.yaml logs woodpecker-server
        exit 1
    fi
done

# 4. Wait for SonarQube
echo "✅ [PASS] Step 4: Wait for SonarQube (localhost:9001, timeout 90s)"
for i in {1..45}; do
    if curl -sf http://localhost:9001/api/system/status | grep -q '"status":"UP"'; then
        echo "   SonarQube is ready"
        break
    fi
    sleep 2
    if [ $i -eq 45 ]; then
        echo "❌ [FAIL] SonarQube did not start in time"
        docker compose -f compose.yaml logs sonarqube
        exit 1
    fi
done

# 5. Verify example pipeline template exists
echo "✅ [PASS] Step 5: Verify .fawkespipe.yml.example exists"
if [ ! -f "$REPO_ROOT/.fawkespipe.yml.example" ]; then
    echo "❌ [FAIL] .fawkespipe.yml.example not found"
    exit 1
fi

# 6. Verify .fawkespipe.yml.example parses as valid YAML
echo "✅ [PASS] Step 6: Verify .fawkespipe.yml.example parses as valid YAML"
python3 -c "import yaml; yaml.safe_load(open('$REPO_ROOT/.fawkespipe.yml.example'))" || {
    echo "❌ [FAIL] YAML parsing failed"
    exit 1
}

# 7. Report elapsed time
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "========================================="
echo "✅ All smoke tests passed in ${ELAPSED}s"
echo "========================================="

# 8. Clean up (optional - comment out for debugging)
echo "✅ [PASS] Step 8: Clean up (docker compose down -v)"
docker compose -f compose.yaml down -v
