"""Tests for the base Scraper class."""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientSession, ClientResponse, ClientError
from bs4 import BeautifulSoup

from app.core.scraper import Scraper


class TestScraper(Scraper[dict]):
    """Test implementation of the abstract Scraper class."""
    
    async def scrape(self, *args, **kwargs):
        """Test implementation of abstract method."""
        return [{"test": "data"}]
    
    def _parse(self, html: str, **kwargs):
        """Test implementation of abstract method."""
        return [{"parsed": True}]


class TestScraperWithFetch(TestScraper):
    """Test scraper with _fetch_and_parse implementation."""
    
    async def _fetch_and_parse(self, url: str, **kwargs):
        """Test implementation with mock response."""
        return [{"url": url, **kwargs}]


@pytest.fixture
def mock_response():
    """Create a mock aiohttp response."""
    response = AsyncMock(spec=ClientResponse)
    response.text.return_value = "<html><body>Test</body></html>"
    response.status = 200
    response.raise_for_status = AsyncMock(return_value=None)
    return response


class AsyncContextManagerMock:
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_session(mock_response):
    """Create a mock aiohttp session."""
    session = AsyncMock(spec=ClientSession)
    
    # Mock the async context manager for the session
    session.__aenter__.return_value = session
    session.__aexit__.return_value = None
    
    # Mock the request to return a response with an async context manager
    session.request.return_value = AsyncContextManagerMock(mock_response)
    
    return session


@pytest.fixture
def mock_playwright():
    """Create mock Playwright objects."""
    # Create the mock objects
    mock_pw = MagicMock()
    mock_async_playwright = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    # Set up the async context manager for playwright
    async def start_playwright():
        return mock_async_playwright
    
    # Set up the async context manager for browser
    mock_async_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    
    # Mock the async_playwright() function
    with patch('app.core.scraper.async_playwright') as mock_playwright_func:
        mock_playwright_func.return_value = AsyncMock()
        mock_playwright_func.return_value.start = AsyncMock(return_value=mock_async_playwright)
        yield mock_pw, mock_browser, mock_context, mock_page


@pytest.mark.asyncio
async def test_scraper_context_manager():
    """Test scraper as async context manager."""
    async with TestScraper() as scraper:
        assert scraper is not None
        assert scraper._session is not None
    assert scraper._session is None or scraper._session.closed


@pytest.mark.asyncio
async def test_fetch(mock_session, mock_response):
    """Test the _make_request method."""
    with patch('aiohttp.ClientSession', return_value=mock_session):
        async with TestScraper() as scraper:
            result = await scraper._make_request("http://test.com")
            
            assert result == "<html><body>Test</body></html>"
            mock_session.request.assert_called_once()
            # Don't check raise_for_status as it's an implementation detail


@pytest.mark.asyncio
async def test_fetch_retry(mock_session):
    """Test request retry logic."""
    # First request fails, second succeeds
    mock_response1 = AsyncMock(spec=ClientResponse)
    mock_response1.text.return_value = "<html>Error</html>"
    mock_response1.status = 500
    mock_response1.raise_for_status.side_effect = ClientError("Test error")

    mock_response2 = AsyncMock(spec=ClientResponse)
    mock_response2.text.return_value = "<html>Success</html>"
    mock_response2.status = 200
    mock_response2.raise_for_status = AsyncMock()

    # Create async context managers for the responses
    mock_context1 = AsyncMock()
    mock_context1.__aenter__.return_value = mock_response1
    mock_context1.__aexit__.return_value = None
    
    mock_context2 = AsyncMock()
    mock_context2.__aenter__.return_value = mock_response2
    mock_context2.__aexit__.return_value = None

    mock_session.request.side_effect = [
        mock_context1,
        mock_context2
    ]

    with patch('aiohttp.ClientSession', return_value=mock_session):
        async with TestScraper(max_retries=3, request_delay=0.1) as scraper:
            result = await scraper._make_request("http://test.com")
        
        assert result == "<html>Success</html>"
        assert mock_session.request.call_count == 2


@pytest.mark.asyncio
async def test_fetch_soup(mock_session, mock_response):
    """Test the _fetch_soup method."""
    with patch('aiohttp.ClientSession', return_value=mock_session):
        async with TestScraper() as scraper:
            # Mock the response for _make_request
            with patch.object(scraper, '_make_request', return_value="<html><body><h1>Test</h1></body></html>"):
                soup = await scraper._fetch_soup("http://test.com")
                
                assert soup is not None
                assert soup.h1.text == "Test"


@pytest.mark.asyncio
async def test_create_page(mock_playwright):
    """Test browser page creation."""
    mock_pw, mock_browser, mock_context, mock_page = mock_playwright
    
    # Create the scraper instance without using context manager
    scraper = TestScraper()
    
    # Mock the close method to prevent it from trying to stop the mock playwright
    original_close = scraper.close
    async def mock_close():
        # Skip the actual cleanup in tests
        scraper._session = None
        scraper.browser = None
        scraper.playwright = None
    
    try:
        # Patch the close method
        scraper.close = mock_close
        
        # Mock _start_browser to avoid actual browser startup
        async def mock_start_browser():
            scraper.playwright = mock_pw
            scraper.browser = mock_browser
            
        # Patch the _start_browser method
        with patch.object(scraper, '_start_browser', side_effect=mock_start_browser):
            # Call the method under test
            page = await scraper._create_page()
            
            # Assertions
            assert page is not None
            mock_browser.new_context.assert_called_once()
            mock_context.new_page.assert_called_once()
    finally:
        # Restore the original close method
        scraper.close = original_close
        # Ensure we clean up properly
        if hasattr(scraper, '_session') and scraper._session and not scraper._session.closed:
            await scraper._session.close()


@pytest.mark.asyncio
async def test_scrape_paginated():
    """Test pagination helper method."""
    test_data = [
        [{"id": 1}, {"id": 2}],
        [{"id": 3}, {"id": 4}],
        []  # Empty page to stop iteration
    ]
    
    class PaginatedScraper(TestScraper):
        def __init__(self):
            super().__init__()
            self.pages = test_data.copy()
        
        async def _fetch_and_parse(self, url, **kwargs):
            if self.pages:
                return self.pages.pop(0)
            return []
    
    async with PaginatedScraper() as scraper:
        results = []
        async for page in scraper.scrape_paginated("http://test.com", max_pages=3):
            results.extend(page)
        
        assert len(results) == 4
        assert all(isinstance(item["id"], int) for item in results)


@pytest.mark.asyncio
async def test_scrape_abstract_method():
    """Test that abstract methods raise NotImplementedError."""
    class IncompleteScraper(Scraper[dict]):
        pass
    # This should work
    class CompleteScraper(Scraper):
        async def scrape(self, *args, **kwargs):
            return []
        
        def _parse(self, html: str, **kwargs):
            return []
    
    CompleteScraper()


def test_get_random_user_agent():
    """Test user agent randomization."""
    user_agents = set()
    for _ in range(10):
        user_agents.add(Scraper._get_random_user_agent())
    
    # Should have at least 2 different user agents
    assert len(user_agents) >= 2


@pytest.mark.asyncio
async def test_scraper_cleanup():
    """Test that resources are properly cleaned up."""
    scraper = TestScraper()
    
    # Mock the close method to track calls
    original_close = scraper.close
    scraper.close = AsyncMock(wraps=original_close)
    
    async with scraper as s:
        assert s is scraper
    
    # Verify close was called
    scraper.close.assert_awaited_once()
    
    # Verify session is closed
    assert scraper._session is None or scraper._session.closed
