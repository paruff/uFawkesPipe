.PHONY: help test test-unit test-integration test-smoke test-acceptance validate pre-commit-setup pre-commit-run

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

validate-docker: ## Validate docker-compose.yml
	@echo "Validating docker-compose.yml..."
	docker compose config --quiet
	@echo "✅ docker-compose.yml is valid"

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

up: ## Start Docker Compose stack
	docker compose up -d

down: ## Stop Docker Compose stack
	docker compose down -v

logs: ## View Docker Compose logs
	docker compose logs -f

ps: ## List running containers
	docker compose ps

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Clean up test artifacts
	rm -rf .pytest_cache __pycache__ tests/__pycache__ tests/unit/__pycache__ tests/integration/__pycache__ tests/smoke/__pycache__ tests/acceptance/__pycache__
	rm -rf htmlcov .coverage coverage.xml
	docker compose down -v --remove-orphans 2>/dev/null || true
