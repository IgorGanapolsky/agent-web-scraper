.PHONY: help install test lint typecheck check clean

# Default target
help:
	@echo "Please use 'make <target>' where <target> is one of:"
	@echo "  install     Install dependencies and setup development environment"
	@echo "  test       Run tests"
	@echo "  test-cov   Run tests with coverage report"
	@echo "  lint       Run code style checks"
	@echo "  typecheck  Run static type checking"
	@echo "  check      Run all checks (lint, typecheck, test)"
	@echo "  format     Format code using black and isort"
	@echo "  clean      Clean up temporary files"

# Install dependencies
install:
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install
	playwright install

# Run tests
test:
	pytest tests/

# Run tests with coverage
test-cov:
	pytest --cov=app --cov-report=term-missing tests/

# Run code style checks
lint:
	black --check .
	isort --check-only .
	flake8 .

# Run static type checking
typecheck:
	mypy .

# Run all checks
check: lint typecheck test

# Format code
format:
	black .
	isort .


# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	rm -rf .coverage htmlcov/ build/ dist/ *.egg-info/
