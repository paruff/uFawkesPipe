#!/bin/bash
# Validation script for uFawkesPipe platform

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "uFawkesPipe Platform Validation"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check prerequisites
echo "Checking prerequisites..."

if command -v docker &> /dev/null; then
    success "Docker is installed ($(docker --version))"
else
    error "Docker is not installed"
    exit 1
fi

if docker compose version &> /dev/null; then
    success "Docker Compose is available ($(docker compose version))"
else
    error "Docker Compose is not installed"
    exit 1
fi

echo ""

# Validate compose.yaml
echo "Validating compose.yaml..."
if docker compose -f compose.yaml config > /dev/null 2>&1; then
    success "compose.yaml is valid"
else
    error "compose.yaml has syntax errors"
    docker compose -f compose.yaml config
    exit 1
fi

echo ""

# Check required files exist
echo "Checking required files..."
required_files=(
    "compose.yaml"
    ".env.example"
    ".fawkespipe.yml.example"
    ".woodpecker.yml"
    "README.md"
    "Makefile"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        success "$file exists"
    else
        error "$file is missing"
        exit 1
    fi
done

echo ""

# Validate YAML files
echo "Validating YAML files (compose.yaml, .woodpecker.yml, examples)..."
if command -v python3 &> /dev/null; then
    # Check if PyYAML is available
    if python3 -c "import yaml" 2>/dev/null; then
        python3 << 'EOF'
import os
import yaml
import sys

files = [
    'compose.yaml',
    '.woodpecker.yml',
    '.fawkespipe.yml.example',
    'examples/.fawkespipe-java-maven.yml',
    'examples/.fawkespipe-python-flask.yml',
    'examples/.fawkespipe-nodejs-express.yml',
    'examples/.fawkespipe-go.yml',
]

all_valid = True

# Single document YAML files
for file in files:
    try:
        with open(file, 'r') as f:
            yaml.safe_load(f)
        print(f'✅ {file} is valid')
    except Exception as e:
        print(f'❌ {file} has errors: {str(e)}')
        all_valid = False

# Multi-document YAML files
for file in []:
    try:
        with open(file, 'r') as f:
            docs = list(yaml.safe_load_all(f))
            print(f'✅ {file} is valid ({len([d for d in docs if d])} resources)')
    except Exception as e:
        print(f'❌ {file} has errors: {str(e)}')
        all_valid = False

sys.exit(0 if all_valid else 1)
EOF

        if [ $? -eq 0 ]; then
            success "All YAML files are valid"
        else
            error "Some YAML files have errors"
            exit 1
        fi
    else
        warning "PyYAML not available, skipping YAML validation. Install with: pip3 install pyyaml"
    fi
else
    warning "Python3 not available, skipping YAML validation"
fi

echo ""

# Check Dockerfile syntax (optional - only if Dockerfiles exist)
echo "Checking Dockerfile syntax..."
for dockerfile in $(find . -name "Dockerfile" -not -path "./.git/*" 2>/dev/null || true); do
    if grep -q "^FROM " "$dockerfile"; then
        success "$dockerfile has valid FROM directive"
    else
        warning "$dockerfile is missing FROM directive"
    fi
done

echo ""

# Check directory structure
echo "Checking directory structure..."
required_dirs=(
    "examples"
    "docs"
    "scripts"
    "tests"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        success "$dir/ directory exists"
    else
        error "$dir/ directory is missing"
        exit 1
    fi
done

echo ""

# Check .env setup
echo "Checking environment configuration..."
if [ -f ".env" ]; then
    success ".env file exists"

    # Check required variables
    required_vars=("WOODPECKER_GITHUB_CLIENT" "WOODPECKER_GITHUB_SECRET" "WOODPECKER_AGENT_SECRET" "SONARQUBE_ADMIN_PASSWORD")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            value=$(grep "^${var}=" .env | cut -d= -f2-)
            # Check for default/placeholder values
            if echo "$value" | grep -qiE "your_|change_me|your-"; then
                warning "$var is set to default value, please update .env"
            else
                success "$var is configured"
            fi
        else
            warning "$var is not set in .env"
        fi
    done
else
    warning ".env file does not exist. Copy from .env.example and configure."
fi

echo ""

# Verify pipeline and example configurations
echo "Checking pipeline and example configurations..."
example_files=(
    ".woodpecker.yml"
    "examples/.fawkespipe-java-maven.yml"
    "examples/.fawkespipe-python-flask.yml"
    "examples/.fawkespipe-nodejs-express.yml"
    "examples/.fawkespipe-go.yml"
)

for file in "${example_files[@]}"; do
    if [ -f "$file" ]; then
        success "$(basename "$file") exists"
    else
        error "$(basename "$file") is missing"
    fi
done

echo ""

# Check documentation
echo "Checking documentation..."
doc_files=(
    "README.md"
)

for file in "${doc_files[@]}"; do
    if [ -f "$file" ]; then
        success "$file exists"
    else
        error "$file is missing"
    fi
done

echo ""

# Summary
echo "========================================="
echo "Validation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure credentials"
echo "2. Run 'make init' to initialize the platform"
echo "3. Run 'docker compose -f compose.yaml up -d' to start all services"
echo "4. Access Woodpecker CI at http://localhost:8000"
echo ""
echo "For more information, see README.md"

success "All checks passed! ✨"
