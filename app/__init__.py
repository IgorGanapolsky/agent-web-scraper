"""Agent Web Scraper - A powerful web scraping tool with AI capabilities."""

__version__ = '0.1.0'

# Import core modules to make them available at the package level
# Importing modules here to avoid circular imports
import importlib

# Lazy loading modules to prevent circular imports
_modules = {}

def __getattr__(name):
    if name in ['cli', 'config', 'core', 'ui', 'utils', 'api', 'observability']:
        if name not in _modules:
            _modules[name] = importlib.import_module(f'.{name}', __name__)
        return _modules[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'cli',
    'config',
    'core',
    'ui',
    'utils',
    'api',
    'observability',
    '__version__',
]
