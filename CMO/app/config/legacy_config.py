"""Legacy configuration compatibility layer."""

import warnings

from app.config.settings import settings

# Backward compatibility - deprecated, use app.config.settings instead
warnings.warn(
    "Using config.py is deprecated. Please use 'from app.config.settings import settings' instead.",
    DeprecationWarning,
    stacklevel=2,
)

SERPAPI_KEY = settings.serpapi_key
OPENAI_API_KEY = settings.openai_api_key
SPREADSHEET_NAME = settings.spreadsheet_name
