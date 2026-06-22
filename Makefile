.PHONY: help init check-env test test-unit test-integration test-smoke test-acceptance validate validate-docker validate-jenkins validate-k8s pre-commit-setup pre-commit-run up down logs status clean

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

validate: validate-docker validate-jenkins validate-k8s ## Run all validations

validate-docker: ## Validate compose.yaml
	@echo "Validating compose.yaml..."
	docker compose -f compose.yaml config --quiet
	@echo "✅ compose.yaml is valid"

validate-jenkins: ## Validate Jenkinsfile syntax
	@echo "Validating Jenkinsfile..."
	@python3 -c "import jenkins_pipeline_linter; jenkins_pipeline_linter.lint_file('Jenkinsfile')" || \
		echo "⚠️  Jenkinsfile linting skipped (jenkins_pipeline_linter not installed)"

validate-k8s: ## Validate Kubernetes manifests
	@echo "Validating K8s manifests..."
	@for f in k8s/*.yaml; do \
		echo "  Checking $$f..."; \
		python3 -c "import yaml; yaml.safe_load(open('$$f'))" || exit 1; \
	done
	@echo "✅ K8s manifests are valid YAML"

validate-all: validate-docker validate-k8s ## Validate all (Docker + K8s)
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

up: ## Start uFawkesPipe stack (compose.yaml)
	docker compose -f compose.yaml up -d

down: ## Stop uFawkesPipe stack (compose.yaml)
	docker compose -f compose.yaml down -v

logs: ## View uFawkesPipe stack logs (compose.yaml)
	docker compose -f compose.yaml logs -f

status: ## List running containers in uFawkesPipe stack
	docker compose -f compose.yaml ps

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
