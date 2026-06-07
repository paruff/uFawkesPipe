# Makefile for uFawkesPipe platform management

.PHONY: help start stop restart logs status clean build ps health backup restore

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

start: ## Start all services
	@echo "🚀 Starting uFawkesPipe platform..."
	docker-compose up -d
	@echo "✅ Platform started. Access Jenkins at http://localhost:8080/jenkins"

stop: ## Stop all services
	@echo "🛑 Stopping uFawkesPipe platform..."
	docker-compose stop

down: ## Stop and remove containers
	@echo "🗑️  Removing uFawkesPipe containers..."
	docker-compose down

restart: ## Restart all services
	@echo "🔄 Restarting uFawkesPipe platform..."
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-jenkins: ## Show Jenkins logs
	docker-compose logs -f jenkins

logs-sonar: ## Show SonarQube logs
	docker-compose logs -f sonarqube

status: ## Show status of all services
	docker-compose ps

ps: status ## Alias for status

health: ## Check health of all services
	@echo "🏥 Checking service health..."
	@if command -v jq &> /dev/null; then \
		docker-compose ps --format json | jq -r '.[] | "\(.Name): \(.Status)"'; \
	else \
		docker-compose ps; \
	fi

build: ## Build custom images
	@echo "🏗️  Building custom images..."
	docker-compose build

clean: ## Remove all containers, volumes, and images
	@echo "⚠️  WARNING: This will remove all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker system prune -af; \
		echo "✅ Cleanup complete"; \
	fi

backup: ## Backup Jenkins data
	@echo "💾 Backing up Jenkins data..."
	@mkdir -p backups
	docker run --rm -v ufp_jenkins_home:/data -v $(PWD)/backups:/backup alpine \
		tar czf /backup/jenkins-backup-$$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
	@echo "✅ Backup complete: backups/jenkins-backup-*.tar.gz"

restore: ## Restore Jenkins data from latest backup
	@echo "🔄 Restoring Jenkins data from backup..."
	@if [ -z "$$(ls -A backups/jenkins-backup-*.tar.gz 2>/dev/null)" ]; then \
		echo "❌ No backup files found in backups/"; \
		exit 1; \
	fi
	@LATEST=$$(ls -t backups/jenkins-backup-*.tar.gz | head -1); \
	echo "Restoring from: $$LATEST"; \
	docker-compose stop jenkins; \
	docker run --rm -v ufp_jenkins_home:/data -v $(PWD)/backups:/backup alpine \
		sh -c "rm -rf /data/* && tar xzf /backup/$$(basename $$LATEST) -C /data"; \
	docker-compose start jenkins; \
	echo "✅ Restore complete"

validate-config: ## Validate docker-compose configuration
	docker-compose config

init: ## Initialize environment (first-time setup)
	@echo "🎬 Initializing uFawkesPipe platform..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file. Please edit it with your credentials."; \
	else \
		echo "ℹ️  .env file already exists"; \
	fi
	@mkdir -p shared shared/reports
	@echo "✅ Created shared directories"
	@echo ""
	@echo "📝 Next steps:"
	@echo "   1. Edit .env with your credentials"
	@echo "   2. Run 'make start' to start the platform"
	@echo "   3. Access Jenkins at http://localhost:8080/jenkins"

update: ## Update images to latest versions
	@echo "⬆️  Updating images..."
	docker-compose pull
	docker-compose up -d

dev: ## Start in development mode with logs
	docker-compose up

test-webhook: ## Test webhook endpoint (requires jq)
	@echo "🔔 Testing webhook endpoint..."
	@if [ -f .env ]; then \
		WEBHOOK_SECRET=$$(grep "^WEBHOOK_SECRET=" .env | cut -d= -f2-); \
	else \
		WEBHOOK_SECRET="changeme"; \
		echo "⚠️  Using default webhook secret. Configure .env for actual secret."; \
	fi; \
	if command -v jq &> /dev/null; then \
		curl -X POST "http://localhost:8080/jenkins/generic-webhook-trigger/invoke" \
			-H "Content-Type: application/json" \
			-d "{\"test\": \"true\", \"webhook_secret\": \"$$WEBHOOK_SECRET\"}" | jq .; \
	else \
		curl -X POST "http://localhost:8080/jenkins/generic-webhook-trigger/invoke" \
			-H "Content-Type: application/json" \
			-d "{\"test\": \"true\", \"webhook_secret\": \"$$WEBHOOK_SECRET\"}"; \
	fi

wait-for-jenkins: ## Wait for Jenkins to be ready
	@echo "⏳ Waiting for Jenkins to be ready..."
	@until curl -s -f http://localhost:8080/jenkins/login >/dev/null 2>&1; do \
		echo "  Jenkins not ready yet..."; \
		sleep 5; \
	done
	@echo "✅ Jenkins is ready!"

wait-for-sonar: ## Wait for SonarQube to be ready
	@echo "⏳ Waiting for SonarQube to be ready..."
	@until curl -s http://localhost:9000/api/system/status | grep -q '"status":"UP"'; do \
		echo "  SonarQube not ready yet..."; \
		sleep 5; \
	done
	@echo "✅ SonarQube is ready!"

wait-all: wait-for-jenkins wait-for-sonar ## Wait for all services to be ready
	@echo "🎉 All services are ready!"
