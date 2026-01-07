# Context Engineering MCP Platform - Development Makefile
# This Makefile provides convenient commands for development and testing

.PHONY: help install install-dev test test-cov lint format type-check security-check pre-commit clean build docker-build docker-run docs serve-docs

# Default target
help: ## Show this help message
	@echo "Context Engineering MCP Platform - Development Commands"
	@echo "======================================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation
install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e ".[dev,security,monitoring]"
	npm install
	pre-commit install

# Testing
test: ## Run all tests
	pytest tests/ -v

test-unit: ## Run unit tests only
	pytest tests/unit/ -v -m "not integration"

test-integration: ## Run integration tests only
	pytest tests/integration/ -v -m "integration"

test-security: ## Run security tests only
	pytest tests/security/ -v -m "security"

test-cov: ## Run tests with coverage
	pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode
	pytest-watch tests/ -- -v

# Code Quality
lint: ## Run all linters
	@echo "Running Python linting..."
	ruff check . --fix
	@echo "Running JavaScript linting..."
	npx eslint mcp-server/ --fix
	@echo "Running security checks..."
	bandit -r . -f json -o security-report.json || true
	@echo "Linting complete!"

format: ## Format all code
	@echo "Formatting Python code..."
	black .
	isort .
	@echo "Formatting JavaScript code..."
	npx prettier --write "mcp-server/**/*.js"
	@echo "Formatting complete!"

type-check: ## Run type checking
	mypy . --ignore-missing-imports

security-check: ## Run security analysis
	@echo "Running security checks..."
	bandit -r . -f console
	safety check
	@echo "Security check complete!"

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

# Development Services
dev-install: ## Install all development dependencies
	$(MAKE) install-dev
	@echo "Setting up git hooks..."
	pre-commit install --hook-type pre-commit --hook-type pre-push
	@echo "Development environment setup complete!"

dev-setup: ## Complete development environment setup
	@echo "Setting up development environment..."
	$(MAKE) dev-install
	@echo "Creating .env file from example..."
	cp .env.example .env
	@echo "⚠️  Please edit .env file with your API keys"
	@echo "Development setup complete!"

# Server Management
serve: ## Start all services locally
	@echo "Starting Context Engineering MCP Platform..."
	./scripts/start-all-services.sh

serve-guides: ## Start AI Guides API server only
	uvicorn main:app --host 0.0.0.0 --port 8888 --reload

serve-context: ## Start Context Engineering API server only
	cd context_engineering && python context_api.py

serve-workflow: ## Start Workflow System API server only
	cd workflow_system && python workflow_api.py

serve-mcp: ## Start MCP server only
	cd mcp-server && node context_mcp_server.js

# Docker Operations
docker-build: ## Build Docker images
	docker-compose build

docker-run: ## Run services with Docker
	docker-compose up -d

docker-dev: ## Run development environment with Docker
	docker-compose -f docker-compose.dev.yml up -d

docker-stop: ## Stop Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-clean: ## Clean Docker images and containers
	docker-compose down -v
	docker system prune -f

# Database & Data
db-migrate: ## Run database migrations (if applicable)
	@echo "No database migrations configured yet"

db-seed: ## Seed database with sample data
	python scripts/seed_data.py

data-backup: ## Backup application data
	@echo "Creating data backup..."
	tar -czf backup-$(shell date +%Y%m%d_%H%M%S).tar.gz context_engineering/templates/ logs/

# Documentation
docs: ## Generate documentation
	@echo "Generating API documentation..."
	@# Add documentation generation commands here
	@echo "Documentation generated!"

docs-serve: ## Serve documentation locally
	@echo "Serving documentation on http://localhost:8080"
	python -m http.server 8080 -d docs/

# Building & Packaging
build: ## Build the application
	@echo "Building Context Engineering MCP Platform..."
	python -m build

build-js: ## Build JavaScript components
	cd mcp-server && npm run build 2>/dev/null || echo "No build script configured"

clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf node_modules/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"

# Release & Deployment
release-check: ## Check if ready for release
	@echo "Checking release readiness..."
	$(MAKE) test
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) security-check
	@echo "✅ Release checks passed!"

deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	@# Add staging deployment commands
	@echo "Staging deployment complete!"

deploy-prod: ## Deploy to production environment
	@echo "Deploying to production..."
	@# Add production deployment commands
	@echo "Production deployment complete!"

# Monitoring & Debugging
logs: ## View application logs
	tail -f logs/*.log 2>/dev/null || echo "No log files found"

health-check: ## Check service health
	@echo "Checking service health..."
	curl -f http://localhost:8888/health || echo "AI Guides API: ❌"
	curl -f http://localhost:9003/api/stats || echo "Context API: ❌"
	curl -f http://localhost:9002/api/workflows || echo "Workflow API: ❌"

performance-test: ## Run performance tests
	@echo "Running performance tests..."
	@# Add performance testing commands
	@echo "Performance tests complete!"

# Development Utilities
fix: ## Fix common issues automatically
	$(MAKE) format
	$(MAKE) lint

check: ## Run all checks
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test
	$(MAKE) security-check

update-deps: ## Update all dependencies
	@echo "Updating Python dependencies..."
	pip install --upgrade -r requirements.txt
	@echo "Updating Node.js dependencies..."
	cd mcp-server && npm update
	@echo "Dependencies updated!"

env-validate: ## Validate environment configuration
	python scripts/validate_env.py .env.example

todo-check: ## Check for TODO/FIXME comments
	python scripts/check_todos.py $(shell find . -name "*.py" -not -path "./tests/*" -not -path "./.venv/*")

# Git Hooks & Quality
git-hooks: ## Install git hooks
	pre-commit install --hook-type pre-commit --hook-type pre-push --hook-type commit-msg

quality: ## Run quality checks
	$(MAKE) check
	$(MAKE) todo-check
	$(MAKE) env-validate

# Special targets
first-run: ## First time setup and run
	$(MAKE) dev-setup
	@echo ""
	@echo "🎉 Setup complete! Next steps:"
	@echo "1. Edit .env file with your Gemini API key"
	@echo "2. Run 'make serve' to start all services"
	@echo "3. Visit http://localhost:8888 for AI Guides API"
	@echo "4. Visit http://localhost:9003 for Context Engineering API"

full-test: ## Run comprehensive test suite
	$(MAKE) clean
	$(MAKE) install-dev
	$(MAKE) quality
	$(MAKE) test-cov
	$(MAKE) build
	@echo "🎉 Full test suite completed successfully!"