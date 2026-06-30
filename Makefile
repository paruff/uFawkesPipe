.PHONY: help init check-env test test-unit test-integration test-smoke test-acceptance validate validate-docker validate-k8s validate-suite pre-commit-setup pre-commit-run up up-suite down down-suite logs logs-suite status status-suite clean network

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Test Commands
# ============================================================================

test: test-unit ## Run all tests
	@echo "All tests passed"

test-unit: ## Run unit tests
	pytest tests/unit/ -v --tb=short

test-integration: ## Run integration tests (requires Docker)
	pytest tests/integration/ -v --tb=short

test-smoke: ## Run smoke tests (requires running stack)
	pytest tests/smoke/ -v --tb=short

test-acceptance: ## Run acceptance tests (requires running stack)
	pytest tests/acceptance/ -v --tb=short

test-coverage: ## Run tests with coverage report
	pytest tests/unit/ -v --tb=short --cov=tests/unit --cov-report=term-missing

# ============================================================================
# Validation Commands
# ============================================================================

validate: validate-docker validate-k8s ## Run all validations (Docker + K8s)

validate-docker: ## Validate compose.yaml
	@echo "Validating compose.yaml..."
	docker compose -f compose.yaml config --quiet
	@echo "✅ compose.yaml is valid"

validate-k8s: ## Validate Kubernetes manifests (supports multi-document YAML)
	@echo "Validating K8s manifests..."
	@for f in k8s/*.yaml; do \
		res=$$(python3 -c "import yaml; docs=list(yaml.safe_load_all(open('$$f'))); print(f'  ✅ $$f ({len([d for d in docs if d])} resources)')" 2>&1) || exit 1; \
		echo "$$res"; \
	done
	@echo "✅ K8s manifests are valid YAML"

validate-suite: validate-docker ## Validate suite mode (compose.yaml + compose.suite.yaml)
	@echo "Validating suite mode compose files..."
	docker compose -f compose.yaml -f compose.suite.yaml config --quiet
	@echo "✅ compose.yaml + compose.suite.yaml composition is valid"

validate-all: validate-docker validate-k8s validate-suite ## Validate all (Docker + K8s + Suite)
	@echo "✅ All validations passed"

# ============================================================================
# Pre-commit Commands
# ============================================================================

pre-commit-setup: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install

pre-commit-run: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# ============================================================================
# Docker Commands
# ============================================================================

network: ## Ensure fawkes-net Docker network exists
	docker network create fawkes-net 2>/dev/null || true

up: network ## Start uFawkesPipe stack — standalone mode (compose.yaml)
	docker compose -f compose.yaml up -d

down: ## Stop uFawkesPipe stack — standalone mode (compose.yaml)
	docker compose -f compose.yaml down -v

logs: ## View uFawkesPipe stack logs — standalone mode (compose.yaml)
	docker compose -f compose.yaml logs -f

status: ## List running containers — standalone mode
	docker compose -f compose.yaml ps

# ============================================================================
# Suite Mode — connects to uFawkesRes + uFawkesObs
# Prerequisites: uFawkesRes and uFawkesObs stacks must be running
#   cd ../uFawkesRes && make up
#   cd ../uFawkesObs && make up
# ============================================================================

up-suite: ## Start uFawkesPipe stack — suite mode (compose + compose.suite)
	@echo "ℹ️  Suite mode requires uFawkesRes and uFawkesObs to be running."
	@echo "   cd ../uFawkesRes && make up"
	@echo "   cd ../uFawkesObs && make up"
	@echo ""
	docker compose -f compose.yaml -f compose.suite.yaml up -d

down-suite: ## Stop uFawkesPipe stack — suite mode (compose + compose.suite)
	docker compose -f compose.yaml -f compose.suite.yaml down -v

logs-suite: ## View uFawkesPipe stack logs — suite mode
	docker compose -f compose.yaml -f compose.suite.yaml logs -f

status-suite: ## List running containers — suite mode
	docker compose -f compose.yaml -f compose.suite.yaml ps

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Clean up test artifacts
	rm -rf .pytest_cache __pycache__ tests/__pycache__ tests/unit/__pycache__ tests/integration/__pycache__ tests/smoke/__pycache__ tests/acceptance/__pycache__
	rm -rf htmlcov .coverage coverage.xml
	docker compose -f compose.yaml down -v --remove-orphans 2>/dev/null || true

init: ## Initialize .env from .env.example if not present
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env from .env.example — edit it with your secrets"; \
	else \
		echo "⚠️  .env already exists — skipping"; \
	fi

check-env: ## Validate required environment variables
	@echo "Checking required environment variables..."
	@MISSING=0; \
	for var in WOODPECKER_GITHUB_CLIENT WOODPECKER_GITHUB_SECRET WOODPECKER_AGENT_SECRET; do \
		if [ -z "$${!var}" ]; then \
			echo "  ❌ $$var is not set"; \
			MISSING=1; \
		else \
			echo "  ✅ $$var is set"; \
		fi; \
	done; \
	if [ "$$MISSING" -eq 1 ]; then \
		echo "⚠️  Some required variables are missing. Check your .env file."; \
		exit 1; \
	else \
		echo "✅ All required environment variables are set."; \
	fi
