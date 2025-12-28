.PHONY: help install lint lint-fix format format-check typecheck test check clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install       Install dependencies"
	@echo "  lint          Run linter (check only)"
	@echo "  lint-fix      Run linter with auto-fix"
	@echo "  format        Format code"
	@echo "  format-check  Check code formatting"
	@echo "  typecheck     Run type checker"
	@echo "  test          Run tests"
	@echo "  check         Run all checks (lint, format, typecheck, test)"
	@echo "  clean         Remove build artifacts and caches"

install:
	uv sync

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run ty check

test:
	uv run pytest

check: lint format-check typecheck test

clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
