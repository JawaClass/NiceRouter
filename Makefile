 
.PHONY: help lint lint-fix format format-check typecheck check fix
 
help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'
 
lint: ## Run ruff lint (no changes)
	uv run ruff check
 
lint-fix: ## Run ruff lint and apply safe auto-fixes
	uv run ruff check --fix
 
format: ## Format code with ruff
	uv run ruff format
 
format-check: ## Check formatting without changing files
	uv run ruff format --check
 
typecheck: ## Run pyright (skips alembic migrations)
	uv run ty check

test: ## Run pytest
	uv run pytest

db-check: ## Run alembic check of backend
	uv run alembic --config alembic.ini check

fix: lint-fix format ## Auto-fix lint issues and format
 
check:  lint format-check typecheck test ## Run everything read-only (good for CI)
 