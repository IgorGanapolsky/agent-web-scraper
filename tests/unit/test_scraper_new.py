"""Unit tests for the undetected scraper functionality."""
import pytest
import logging
from unittest.mock import patch, MagicMock, ANY
from app.core.undetected_scraper import UndetectedChromeScraper

# Disable logging during tests
logging.disable(logging.CRITICAL)


class MockWebElement:
    """Mock for WebElement"""
    def __init__(self, text):
        self.text = text


class MockUndetectedChrome:
    """Mock for undetected_chromedriver.Chrome"""
    def __init__(self, *args, **kwargs):
        self.options = MagicMock()
        self.service = MagicMock()
        self.page_source = "<html><head><title>Test</title></head><body><h1>Test Header</h1></body>"
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args, **kwargs):
        pass
    
    def get(self, url):
        return self
    
    def find_elements(self, by, value):
        if by == "tag name" and value == "h1":
            return [MockWebElement("Test Header")]
        return []
    
    def quit(self):
        pass
        
    def execute_cdp_cmd(self, cmd, params):
        """Mock CDP command execution"""
        return {}
        
    def add_argument(self, arg):
        """Mock add_argument for options"""
        pass
        
    def execute_script(self, script):
        """Mock execute_script method"""
        return None


class TestUndetectedChromeScraper:
    """Test suite for the UndetectedChromeScraper class."""
    
    @pytest.fixture
    def scraper(self):
        """Create an UndetectedChromeScraper instance for testing."""
        with patch('undetected_chromedriver.Chrome', MockUndetectedChrome), \
             patch('webdriver_manager.chrome.ChromeDriverManager') as mock_manager:
            mock_manager.return_value.install.return_value = "/fake/path/chromedriver"
            scraper = UndetectedChromeScraper(headless=True)
            yield scraper

    def test_initialization(self, scraper):
        """Test that the scraper initializes correctly."""
        assert scraper.driver is not None
        assert scraper.headless is True
    
    def test_scraper_context_manager(self):
        """Test that the scraper works as a context manager."""
        with patch('undetected_chromedriver.Chrome', MockUndetectedChrome), \
             patch('webdriver_manager.chrome.ChromeDriverManager') as mock_manager:
            mock_manager.return_value.install.return_value = "/fake/path/chromedriver"
            with UndetectedChromeScraper() as scraper:
                assert scraper.driver is not None
                assert "Test Header" in scraper.driver.page_source
                
    def test_scraper_find_elements(self, scraper):
        """Test that the scraper can find elements."""
        elements = scraper.driver.find_elements("tag name", "h1")
        assert len(elements) > 0
        assert elements[0].text == "Test Header"
