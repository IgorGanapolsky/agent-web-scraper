# Contributing to Agent Web Scraper

Thank you for your interest in contributing to Agent Web Scraper! We welcome contributions from the community to help improve this project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/agent-web-scraper.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Commit your changes: `git commit -m "Add your commit message"`
6. Push to the branch: `git push origin feature/your-feature-name`
7. Open a pull request

## Development Environment Setup

### Prerequisites

- Python 3.9+
- Poetry (recommended) or pip
- Playwright browsers

### Setup with Poetry (Recommended)


```bash
# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Install Playwright browsers
poetry run playwright install
```

### Setup with pip

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Install Playwright browsers
playwright install
```

## Code Style

We use the following tools to maintain code quality:

- **Black** - Code formatting
- **isort** - Import sorting
- **Flake8** - Linting
- **Mypy** - Static type checking

These tools are automatically run as pre-commit hooks. You can also run them manually:

```bash
# Run all code style checks
make lint

# Run type checking
make typecheck

# Run all checks and tests
make check
```

## Testing

We use pytest for testing. To run the tests:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/unit/test_module.py

# Run a specific test
pytest tests/unit/test_module.py::test_function_name
```

## Pull Request Process

1. Ensure your code passes all tests and linting checks
2. Update the documentation if needed
3. Add tests for new functionality
4. Ensure your branch is up to date with the main branch
5. Open a pull request with a clear description of the changes

## Code Review Process

1. A maintainer will review your pull request
2. You may be asked to make changes
3. Once approved, a maintainer will merge your pull request

## Reporting Issues

Please use the GitHub issue tracker to report bugs or suggest new features. When reporting a bug, please include:

- A clear description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Any relevant error messages

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
