# Core scraping and analysis logic
# (Moved from project root)

from abc import ABC, abstractmethod
from typing import List, Any, Coroutine # Added Coroutine

class Scraper(ABC):
    """
    Abstract base class for scraper implementations.
    """

    @abstractmethod
    async def scrape(self, url: str) -> List[Any]: # Made async, return type is still List[Any] as it's what the coroutine yields
        """
        Scrape data from the given URL.

        Args:
            url: The URL to scrape.

        Returns:
            A list of scraped items. The specific type of items
            can be defined by concrete implementations.
        """
        pass
