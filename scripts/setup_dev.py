#!/usr/bin/env python3
"""
Development Environment Setup Script for Agent Web Scraper

This script automates the setup of the development environment using modern
Python packaging standards with Hatch.
"""

import subprocess
import sys
from pathlib import Path
from security import safe_command


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_step(message: str) -> None:
    """Print a step message with formatting."""
    print(f"{Colors.OKBLUE}📋 {message}{Colors.ENDC}")


def print_success(message: str) -> None:
    """Print a success message with formatting."""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_warning(message: str) -> None:
    """Print a warning message with formatting."""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    """Print an error message with formatting."""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and handle errors gracefully."""
    try:
        print(f"{Colors.OKCYAN}▶️  Running: {' '.join(cmd)}{Colors.ENDC}")
        result = safe_command.run(subprocess.run, cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {' '.join(cmd)}")
        if e.stderr:
            print(e.stderr)
        if check:
            sys.exit(1)
        return e


def check_python_version() -> None:
    """Check if Python version is compatible."""
    print_step("Checking Python version...")

    if sys.version_info < (3, 10):
        print_error(f"Python 3.10+ required, found {sys.version}")
        sys.exit(1)

    print_success(f"Python {sys.version.split()[0]} is compatible")


def install_hatch() -> None:
    """Install Hatch package manager."""
    print_step("Installing Hatch...")

    # Check if hatch is already installed
    try:
        result = subprocess.run(["hatch", "--version"], capture_output=True)
        if result.returncode == 0:
            print_success("Hatch is already installed")
            return
    except FileNotFoundError:
        pass

    # Install hatch
    run_command([sys.executable, "-m", "pip", "install", "hatch"])
    print_success("Hatch installed successfully")


def setup_project_structure() -> None:
    """Ensure project structure is properly set up."""
    print_step("Setting up project structure...")

    # Create necessary directories
    directories = [
        "logs",
        "secrets",
        "tests",
        "docs",
        "app/cli",
        "app/config",
        "app/core",
        "app/observability",
        "app/utils",
        "app/web",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # Create __init__.py files where needed
    init_files = [
        "app/__init__.py",
        "app/cli/__init__.py",
        "app/config/__init__.py",
        "app/core/__init__.py",
        "app/observability/__init__.py",
        "app/utils/__init__.py",
        "app/web/__init__.py",
        "tests/__init__.py",
    ]

    for init_file in init_files:
        init_path = Path(init_file)
        if not init_path.exists():
            init_path.write_text('"""Package initialization."""\n')

    print_success("Project structure created")


def update_app_init() -> None:
    """Update app/__init__.py with version info."""
    print_step("Updating app initialization...")

    app_init_content = '''"""Agent Web Scraper - AI-powered market research automation."""

__version__ = "0.2.0"
__author__ = "Igor Ganapolsky"
__email__ = "your.email@example.com"

from app.config.safe_logger import get_logger, setup_logging

# Set up default logging
setup_logging()
logger = get_logger(__name__)
logger.info(f"Agent Web Scraper v{__version__} initialized")

__all__ = ["__version__", "__author__", "__email__", "get_logger", "setup_logging"]
'''

    Path("app/__init__.py").write_text(app_init_content)
    print_success("App initialization updated")


def create_env_template() -> None:
    """Create or update .env.template file."""
    print_step("Creating environment template...")

    env_template = """# Agent Web Scraper Environment Configuration

# API Keys
SERPAPI_KEY=your_serpapi_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Sentry Configuration (Optional)
SENTRY_DSN=your_sentry_dsn_here
ENVIRONMENT=development

# Google Sheets Configuration
SPREADSHEET_NAME="Reddit Market Research"

# Application Configuration
LOG_LEVEL=INFO
DEBUG=true

# Server Configuration
HOST=localhost
PORT=8000

# Database Configuration (if needed)
DATABASE_URL=sqlite:///./data.db
"""

    if not Path(".env.template").exists():
        Path(".env.template").write_text(env_template)
        print_success("Environment template created")
    else:
        print_success("Environment template already exists")


def setup_hatch_environment() -> None:
    """Set up Hatch development environment."""
    print_step("Setting up Hatch environment...")

    # Create the environment
    run_command(["hatch", "env", "create"])
    print_success("Hatch environment created")


def install_pre_commit() -> None:
    """Install and set up pre-commit hooks."""
    print_step("Setting up pre-commit hooks...")

    # Install pre-commit in the lint environment
    run_command(["hatch", "run", "lint:pip", "install", "pre-commit"])

    # Install the hooks
    if Path(".pre-commit-config.yaml").exists():
        run_command(["hatch", "run", "lint:pre-commit", "install"])
        print_success("Pre-commit hooks installed")
    else:
        print_warning("No .pre-commit-config.yaml found, skipping pre-commit setup")


def run_initial_checks() -> None:
    """Run initial code quality checks."""
    print_step("Running initial code quality checks...")

    try:
        # Run linting
        result = run_command(["hatch", "run", "lint:style"], check=False)
        if result.returncode == 0:
            print_success("Code style checks passed")
        else:
            print_warning("Code style issues found - run 'hatch run lint:fmt' to fix")

        # Run type checking
        result = run_command(["hatch", "run", "lint:typing"], check=False)
        if result.returncode == 0:
            print_success("Type checking passed")
        else:
            print_warning("Type checking issues found")

    except Exception as e:
        print_warning(f"Could not run checks: {e}")


def create_github_actions() -> None:
    """Create GitHub Actions workflow files."""
    print_step("Creating GitHub Actions workflows...")

    # Create .github/workflows directory
    workflows_dir = Path(".github/workflows")
    workflows_dir.mkdir(parents=True, exist_ok=True)

    # CI workflow
    ci_workflow = """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Hatch
      run: pip install hatch

    - name: Run tests
      run: hatch run test-cov

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      if: matrix.python-version == '3.11'
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Install Hatch
      run: pip install hatch

    - name: Run linting
      run: hatch run lint:all

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Run Bandit Security Scan
      uses: securecodewarrior/github-action-bandit@v1
      with:
        config: .bandit
"""

    (workflows_dir / "ci.yml").write_text(ci_workflow)
    print_success("GitHub Actions CI workflow created")


def main() -> None:
    """Main setup function."""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("🚀 Agent Web Scraper - Development Environment Setup")
    print("=" * 55)
    print(f"{Colors.ENDC}")

    try:
        check_python_version()
        install_hatch()
        setup_project_structure()
        update_app_init()
        create_env_template()
        setup_hatch_environment()
        install_pre_commit()
        create_github_actions()
        run_initial_checks()

        print(f"\n{Colors.OKGREEN}{Colors.BOLD}")
        print("🎉 Setup completed successfully!")
        print("=" * 30)
        print(f"{Colors.ENDC}")

        print(f"\n{Colors.OKCYAN}Next steps:{Colors.ENDC}")
        print("1. Copy .env.template to .env and fill in your API keys")
        print("2. Run 'hatch run test' to run tests")
        print("3. Run 'hatch run lint:fmt' to format code")
        print("4. Run 'hatch shell' to activate the development environment")

    except KeyboardInterrupt:
        print_error("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
