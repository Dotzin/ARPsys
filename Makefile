.PHONY: help install-backend install-frontend install-all run-backend run-frontend run-all test-backend test-frontend lint-frontend clean stop

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install-backend: ## Install backend dependencies
	cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

install-all: install-backend install-frontend ## Install all dependencies

run-backend: ## Run backend server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-frontend: ## Run frontend server
	cd frontend && npm run dev

run-all: ## Run both backend and frontend servers concurrently
	@echo "Starting ARPsys..."
	@./run_all.sh

test-backend: ## Run backend tests
	cd backend && python -m pytest tests/ -v

test-frontend: ## Run frontend tests (if any)
	cd frontend && npm test

lint-frontend: ## Run frontend linting
	cd frontend && npm run lint

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -name "*.pyc" -delete

stop: ## Stop all running servers (requires pkill)
	pkill -f "uvicorn" || true
	pkill -f "next" || true
	pkill -f "npm" || true
