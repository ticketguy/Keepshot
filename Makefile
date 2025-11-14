.PHONY: help build up down logs restart clean migrate shell test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build

up: ## Start the stack
	docker-compose up -d
	@echo "KeepShot is running!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "Health: http://localhost:8000/health"

down: ## Stop the stack
	docker-compose down

logs: ## Show logs
	docker-compose logs -f

restart: ## Restart the stack
	docker-compose restart

clean: ## Stop and remove everything (including volumes)
	docker-compose down -v
	@echo "All data removed!"

migrate: ## Run database migrations
	docker-compose exec app alembic upgrade head

shell: ## Open a shell in the app container
	docker-compose exec app /bin/bash

db-shell: ## Open PostgreSQL shell
	docker-compose exec db psql -U keepshot -d keepshot

test: ## Run tests
	docker-compose exec app pytest tests/

dev: ## Run in development mode (with hot reload)
	docker-compose up

init: ## Initialize project (first time setup)
	@echo "Initializing KeepShot..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file - please add your OPENAI_API_KEY"; fi
	@docker-compose up -d
	@echo "Waiting for database..."
	@sleep 5
	@docker-compose exec app alembic upgrade head
	@echo "KeepShot initialized successfully!"
	@echo "API: http://localhost:8000/docs"
