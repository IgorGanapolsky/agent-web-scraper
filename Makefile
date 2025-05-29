.PHONY: help install test lint typecheck check clean format dev setup

# Default target
help:
	@echo "🚀 Agent Web Scraper - Development Commands"
	@echo "============================================="
	@echo "  setup       Set up development environment with Hatch"
	@echo "  install     Install dependencies using Hatch"
	@echo "  dev         Run development server"
	@echo "  test        Run tests"
	@echo "  test-cov    Run tests with coverage report"
	@echo "  lint        Run code style and type checks"
	@echo "  format      Format code using black and ruff"
	@echo "  check       Run all checks (lint, typecheck, test)"
	@echo "  clean       Clean up temporary files and caches"
	@echo "  docs        Build and serve documentation"
	@echo "  health      Check application health"

# Set up development environment
setup:
	@echo "🔧 Setting up development environment..."
	python setup_dev.py

# Install dependencies using Hatch
install:
	@echo "📦 Installing dependencies with Hatch..."
	hatch env create
	hatch run pip list

# Run development server
dev:
	@echo "🏃 Starting development server..."
	hatch run python run.py

# Run tests
test:
	@echo "🧪 Running tests..."
	hatch run test

# Run tests with coverage
test-cov:
	@echo "🧪 Running tests with coverage..."
	hatch run test-cov

# Run linting and type checking
lint:
	@echo "🔍 Running code quality checks..."
	hatch run lint:all

# Format code
format:
	@echo "✨ Formatting code..."
	hatch run lint:fmt

# Run type checking only
typecheck:
	@echo "🔍 Running type checks..."
	hatch run lint:typing

# Run all checks
check: lint test
	@echo "✅ All checks completed!"

# Build documentation
docs:
	@echo "📚 Building documentation..."
	hatch run docs:build

# Serve documentation
docs-serve:
	@echo "📚 Serving documentation..."
	hatch run docs:serve

# Clean up temporary files
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ build/ dist/ *.egg-info/ .hatch/ 2>/dev/null || true
	@echo "✅ Cleanup completed!"

# Health check
health:
	@echo "🏥 Checking application health..."
	hatch run python -c "from app.cli.main import health_check; health_check()"

# Show project info
info:
	@echo "ℹ️  Project Information"
	@echo "====================="
	hatch run agent-scraper info

# Quick development workflow
quick: format lint test
	@echo "🚀 Quick development checks completed!"

# Production build (if needed)
build:
	@echo "🏗️  Building package..."
	hatch build

# Install pre-commit hooks
pre-commit:
	@echo "🪝 Installing pre-commit hooks..."
	hatch run lint:pre-commit install

# Update dependencies
update:
	@echo "⬆️  Updating dependencies..."
	hatch env prune
	hatch env create

# Run security scan
security:
	@echo "🔒 Running security scan..."
	hatch run lint:bandit -r app/

# Show hatch environments
envs:
	@echo "🏗️  Hatch Environments:"
	hatch env show
