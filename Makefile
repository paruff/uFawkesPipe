.PHONY: help init check-env test test-unit test-integration test-smoke test-acceptance validate validate-docker validate-suite validate-agents generate-pipeline check-pipeline pre-commit-setup pre-commit-run fix-and-commit up up-suite down down-suite logs logs-suite status status-suite clean

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

validate: validate-docker validate-agents ## Run all validations (Docker + Agents)

validate-docker: ## Validate compose.yaml
	@echo "Validating compose.yaml..."
	docker compose -f compose.yaml config --quiet
	@echo "✅ compose.yaml is valid"

validate-suite: validate-docker ## Validate suite mode (compose.yaml + compose.suite.yaml)
	@echo "Validating suite mode compose files..."
	docker compose -f compose.yaml -f compose.suite.yaml config --quiet
	@echo "✅ compose.yaml + compose.suite.yaml composition is valid"

validate-all: validate-docker validate-suite validate-agents ## Validate all (Docker + Suite + Agents)
	@echo "✅ All validations passed"

validate-agents: ## Validate agent and skill definitions
	@echo "Validating agent and skill definitions..."
	bash scripts/validate-agents.sh

# ============================================================================
# Pipeline Contract Commands
# ============================================================================

FILE ?= .fawkespipe.yml
OUTPUT ?= .woodpecker.yml

generate-pipeline: ## Generate .woodpecker.yml from .fawkespipe.yml (FILE=path OUTPUT=path to override)
	python3 scripts/generate_woodpecker_yml.py --contract "$(FILE)" --output "$(OUTPUT)"

check-pipeline: ## Check .woodpecker.yml isn't stale relative to .fawkespipe.yml (FILE=path OUTPUT=path to override)
	python3 scripts/generate_woodpecker_yml.py --contract "$(FILE)" --output "$(OUTPUT)" --check

# ============================================================================
# Pre-commit Commands
# ============================================================================

pre-commit-setup: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type pre-push

pre-commit-run: ## Run pre-commit hooks on all files
	pre-commit run --all-files

fix-and-commit: ## Run pre-commit, stage fixes, commit with conventional message
	@pre-commit run --all-files
	@git add -u
	@read -p "Commit message (type(scope): desc): " msg; \
	git commit -m "$$msg"

# ============================================================================
# Docker Commands
# ============================================================================

up: ## Start uFawkesPipe stack — standalone mode (compose.yaml)
	docker compose -f compose.yaml up -d

up-security: ## Start uFawkesPipe stack + security plane (DefectDojo/Infisical/Falco)
	docker compose -f compose.yaml --profile security up -d

down: ## Stop uFawkesPipe stack — standalone mode (compose.yaml)
	docker compose -f compose.yaml down -v

logs: ## View uFawkesPipe stack logs — standalone mode (compose.yaml)
	docker compose -f compose.yaml logs -f

status: ## List running containers — standalone mode
	docker compose -f compose.yaml ps

health: ## Show container health status table — standalone mode
	@echo "Container Health Status (standalone mode):"
	@docker compose -f compose.yaml ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"

health-suite: ## Show container health status table — suite mode
	@echo "Container Health Status (suite mode):"
	@docker compose -f compose.yaml -f compose.suite.yaml ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"

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
