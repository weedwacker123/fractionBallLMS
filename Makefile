.PHONY: help build up down logs shell migrate test lint format seed clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker containers
	docker-compose build

up: ## Start development environment
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	docker-compose exec web python manage.py migrate
	@echo "Development environment is ready at http://localhost:8000"

down: ## Stop development environment
	docker-compose down

logs: ## Show logs
	docker-compose logs -f

shell: ## Open Django shell
	docker-compose exec web python manage.py shell

dbshell: ## Open database shell
	docker-compose exec web python manage.py dbshell

migrate: ## Run database migrations
	docker-compose exec web python manage.py migrate

makemigrations: ## Create database migrations
	docker-compose exec web python manage.py makemigrations

test: ## Run tests
	docker-compose exec web pytest

test-cov: ## Run tests with coverage
	docker-compose exec web pytest --cov=. --cov-report=html

lint: ## Run linting
	docker-compose exec web flake8 .
	docker-compose exec web black --check .
	docker-compose exec web isort --check-only .

format: ## Format code
	docker-compose exec web black .
	docker-compose exec web isort .

seed: ## Seed database with initial data
	docker-compose exec web python manage.py seed_data

seed-content: ## Seed database with content taxonomy and sample data
	docker-compose exec web python manage.py seed_taxonomy

superuser: ## Create superuser
	docker-compose exec web python manage.py createsuperuser

clean: ## Clean up containers and volumes
	docker-compose down -v
	docker system prune -f

install-hooks: ## Install pre-commit hooks
	pre-commit install
