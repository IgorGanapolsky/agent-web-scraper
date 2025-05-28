"""Utility functions for working with environment variables."""
import os


def get_bool_env(var_name: str, default: bool = False) -> bool:
    """
    Get a boolean value from an environment variable.

    Args:
        var_name: The name of the environment variable.
        default: The default value to return if the environment variable is not set.

    Returns:
        The boolean value of the environment variable, or the default value if not set.
    """
    val = os.environ.get(var_name, "").lower()
    if not val:
        return default
    return val in ("true", "t", "yes", "y", "1", "on")