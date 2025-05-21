"""Pytest configuration and shared test fixtures."""
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)  # Set to WARNING to reduce test output noise

# Enable asyncio debug mode for better error messages
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_playwright():
    """Mock Playwright browser instance."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("playwright.async_api.async_playwright", AsyncMock())
        yield


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for API calls."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_session.return_value.__aenter__.return_value = AsyncMock()
        yield mock_session


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        "title": "Senior Software Engineer",
        "company": "Test Company Inc.",
        "location": "Remote",
        "salary": "$120,000 - $150,000",
        "description": "Test job description",
        "url": "https://example.com/job/123",
        "posted_date": "2023-01-01",
        "job_type": "Full-time",
    }


@pytest.fixture
def mock_google_sheets():
    """Mock Google Sheets client and worksheet."""
    with patch("gspread.authorize") as mock_auth:
        mock_client = MagicMock()
        mock_worksheet = MagicMock()
        mock_client.open().worksheet.return_value = mock_worksheet
        mock_auth.return_value = mock_client
        yield mock_worksheet


@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests."""
    # Reset logging
    logging.root.handlers = []
    logging.root.setLevel(logging.WARNING)

    # Configure console logging only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logging.root.addHandler(console_handler)

    # Patch the actual logging setup
    with patch("app.config.logging.setup_logging"):
        yield


@pytest.fixture(autouse=True)
def no_http_requests(monkeypatch):
    """Prevent any HTTP requests during tests."""

    def urlopen_mock(self, *args, **kwargs):
        raise RuntimeError(f"Unexpected HTTP request to: {self.full_url}")

    monkeypatch.setattr("urllib.request.OpenerDirector.open", urlopen_mock)


# Configure pytest-asyncio to be more verbose
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment."""
    # Set test environment variables
    import os

    os.environ["TESTING"] = "True"

    yield

    # Cleanup after tests
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
