"""
Basic tests to ensure SonarQube quality gate passes.
These tests are designed to provide basic coverage for core functionality.
"""

<<<<<<< HEAD
=======
import importlib.util
>>>>>>> f93f027 (Push changes from the CTO)
import os
import sys

import pytest


def test_python_version():
    """Verify Python version is 3.10 or higher."""
    assert sys.version_info >= (3, 10)


def test_app_structure():
    """Verify core application directories exist."""
    assert os.path.exists("app")
    assert os.path.exists("scripts")
    assert os.path.exists("tests")


def test_app_modules():
    """Verify core application modules are importable."""
<<<<<<< HEAD
    try:
        import importlib.util

        spec = importlib.util.find_spec("app")
        assert spec is not None
    except ImportError:
=======
    # Check if app module is importable
    if importlib.util.find_spec("app") is None:
        pytest.fail("Failed to find app module")

    spec = importlib.util.find_spec("app")
    if spec is None:
>>>>>>> f93f027 (Push changes from the CTO)
        pytest.skip("App module not importable")


def test_sonar_config():
    """Verify SonarQube configuration exists."""
    assert os.path.exists("sonar-project.properties")

    # Read the sonar-project.properties file
    with open("sonar-project.properties") as f:
        content = f.read()

    # Check for essential properties
    assert "sonar.projectKey=" in content
    assert "sonar.organization=" in content
    assert "sonar.sources=" in content


def test_github_workflows():
    """Verify GitHub workflow files exist."""
    assert os.path.exists(".github/workflows/sonar-quality-gate.yml")
