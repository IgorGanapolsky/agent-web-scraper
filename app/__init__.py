"""Agent Web Scraper - AI-powered market research automation."""

__version__ = "0.2.0"
__author__ = "Igor Ganapolsky"
__email__ = "your.email@example.com"

from app.config.safe_logger import get_logger, setup_logging

# Set up default logging
setup_logging()
logger = get_logger(__name__)
logger.info(f"Agent Web Scraper v{__version__} initialized")

__all__ = ["__version__", "__author__", "__email__", "get_logger", "setup_logging"]
