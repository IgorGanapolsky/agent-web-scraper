"""
Core functionality for the web scraper application.

This package contains the core components and utilities for web scraping,
including the base scraper class and any related utilities.
"""

from .scraper import Scraper
from .undetected_scraper import UndetectedChromeScraper

__all__ = [
    "Scraper",
    "UndetectedChromeScraper",
]
