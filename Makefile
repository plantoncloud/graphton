.PHONY: help deps test lint typecheck build clean

help:
	@echo "Available targets:"
	@echo "  make deps       - Install dependencies"
	@echo "  make test       - Run test suite"
	@echo "  make lint       - Run ruff linter"
	@echo "  make typecheck  - Run mypy type checker"
	@echo "  make build      - Run all checks (lint + typecheck + test)"
	@echo "  make clean      - Clean cache files"

deps:
	@echo "Installing dependencies with Poetry..."
	poetry install

test:
	@echo "Running tests with pytest..."
	poetry run pytest tests/ -v --cov=graphton --cov-report=term-missing

lint:
	@echo "Running ruff linter..."
	poetry run ruff check .

typecheck:
	@echo "Running mypy type checker..."
	poetry run mypy graphton/

build: lint typecheck test
	@echo "✅ All checks passed!"

clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Clean complete"

