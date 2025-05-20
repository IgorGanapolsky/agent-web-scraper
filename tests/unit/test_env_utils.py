import os
import pytest
from unittest.mock import patch
from app.utils.env_utils import get_bool_env

class TestGetBoolEnv:
    """Test cases for get_bool_env function."""

    @pytest.mark.parametrize("env_value,expected", [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("yes", True),
        ("y", True),
        ("1", True),
        ("on", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("no", False),
        ("n", False),
        ("0", False),
        ("off", False),
        ("", False),
        ("invalid", False),
    ])
    def test_get_bool_env_variations(self, env_value, expected):
        """Test various string inputs for get_bool_env."""
        with patch.dict(os.environ, {"TEST_VAR": env_value}):
            assert get_bool_env("TEST_VAR") == expected

    def test_get_bool_env_default(self):
        """Test get_bool_env with default value."""
        # When env var is not set
        if "TEST_VAR" in os.environ:
            del os.environ["TEST_VAR"]
        assert get_bool_env("TEST_VAR", True) is True
        assert get_bool_env("TEST_VAR", False) is False

    def test_get_bool_env_override_default(self):
        """Test that environment variable overrides default value."""
        with patch.dict(os.environ, {"TEST_VAR": "false"}):
            assert get_bool_env("TEST_VAR", True) is False

    def test_get_bool_env_case_insensitive(self):
        """Test that get_bool_env is case insensitive."""
        with patch.dict(os.environ, {"TEST_VAR": "TrUe"}):
            assert get_bool_env("TEST_VAR") is True
        with patch.dict(os.environ, {"TEST_VAR": "FaLsE"}):
            assert get_bool_env("TEST_VAR") is False
