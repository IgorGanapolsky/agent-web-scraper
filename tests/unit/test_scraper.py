"""Unit tests for the main scraper functionality."""

import json
import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from app.core.scraper import Scraper


class AsyncContextManagerMock:
    """Helper class to mock async context managers."""

    def __init__(self, return_value=None, side_effect=None):
        self.return_value = return_value
        self.side_effect = side_effect

    async def __aenter__(self):
        if self.side_effect and isinstance(self.side_effect, Exception):
            raise self.side_effect
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class ConcreteScraper(Scraper):
    """Concrete implementation of Scraper for testing."""

    async def _fetch_html(self, url: str) -> str:
        """Mock HTML fetching for testing."""
        # In a real scenario, this would fetch HTML from the URL.
        # For testing, we return a fixed HTML string.
        return "<html><body><h1>Mock</h1><p>Mock</p></body></html>"

    async def scrape(self, url: str) -> list:
        """Implementation of the abstract method."""
        # Ensure this condition is properly formatted and not too long
        if not url.startswith(
            (
                "http://",
                "https://",
            )
        ):
            raise ValueError("Invalid URL")

        html = await self._fetch_html(url)
        # Reformatted for clarity
        job_data = self._extract_job_data(html)
        return [job_data] if job_data else []

    def _extract_job_data(self, html: str) -> dict:
        """Implementation of the abstract method."""
        soup = BeautifulSoup(html, "html.parser")

        job_data = {
            "title": "",
            "company": "",
            "location": "",
            "salary": "",
            "description": "",
            "url": "",
            "posted_date": "",
            "job_type": "",
        }

        title_elem = soup.find("h1")
        if title_elem:
            job_data["title"] = title_elem.get_text(strip=True)

        company_elem = soup.find(class_="company")
        if company_elem:
            job_data["company"] = company_elem.get_text(strip=True)

        location_elem = soup.find(class_="location")
        if location_elem:
            job_data["location"] = location_elem.get_text(strip=True)

        salary_elem = soup.find(class_="salary")
        if salary_elem:
            job_data["salary"] = salary_elem.get_text(strip=True)

        desc_elem = soup.find(class_="description")
        if desc_elem:
            job_data["description"] = desc_elem.get_text(strip=True)

        return job_data


class TestScraper:
    """Test suite for the Scraper class."""

    @pytest.fixture
    def scraper(self, mock_session):
        """Create a Scraper instance for testing."""
        # Create a mock session for the scraper
        scraper = ConcreteScraper(headless=True, timeout=10000)
        scraper._session = mock_session
        return scraper

    @pytest.fixture
    def sample_job_data(self):
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
    def mock_response(self):
        """Create a mock response with text attribute."""
        response = AsyncMock()
        response.text.return_value = "<html>Test HTML</html>"
        response.__aenter__.return_value = response
        return response

    @pytest.fixture
    def mock_session(self):
        """Create a mock session with proper async context manager support."""
        # Create a mock session
        session = AsyncMock(spec=ClientSession)

        # Create a default mock response
        mock_response = AsyncMock()
        mock_response.text.return_value = "<html><h1>Test Job</h1></html>"
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.raise_for_status.return_value = None

        # Set up the mock session to return the mock response by default
        session.get.return_value.__aenter__.return_value = mock_response
        session.request.return_value.__aenter__.return_value = mock_response

        # Patch the aiohttp.ClientSession to return our mock session
        with patch("aiohttp.ClientSession", return_value=session):
            yield session

    @pytest.mark.asyncio
    async def test_scrape_with_valid_url(self, scraper, mock_session):
        """Test scraping with a valid URL."""
        test_url = "https://example.com/jobs"

        # Create a new mock response
        mock_response = AsyncMock()
        mock_response.text.return_value = (
            '<html><h1>Test Job</h1><div class="company">Test Co</div></html>'
        )
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.__aenter__.return_value = mock_response

        # Set the mock return value
        mock_session.get.return_value = mock_response

        # Call the method
        result = await scraper.scrape(test_url)

        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Test Job"
        assert result[0]["company"] == "Test Co"

        # Verify the session was used correctly
        mock_session.get.assert_called_once_with(
            test_url, headers=scraper.DEFAULT_HEADERS
        )

        # Ensure the response methods were called
        mock_response.text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_scrape_with_invalid_url(self, scraper):
        """Test scraping with an invalid URL."""
        with pytest.raises(ValueError, match="Invalid URL"):
            await scraper.scrape("not-a-valid-url")

    @pytest.mark.asyncio
    async def test_extract_job_data(self, scraper):
        """Test job data extraction from HTML."""
        test_html = """
        <html>
            <h1>Software Engineer</h1>
            <div class="company">Test Corp</div>
            <div class="location">Remote</div>
            <div class="salary">$100k - $150k</div>
            <div class="description">Job description here</div>
        </html>
        """

        # Call the method directly with test HTML
        result = scraper._extract_job_data(test_html)

        # Verify the extracted data
        assert result["title"] == "Software Engineer"
        assert result["company"] == "Test Corp"
        assert result["location"] == "Remote"
        assert result["salary"] == "$100k - $150k"
        assert "Job description here" in result["description"]

    @pytest.mark.asyncio
    async def test_handle_rate_limiting(self, scraper, mock_session):
        """Test that the scraper handles rate limiting correctly."""
        # Setup
        test_url = "http://example.com"
        mock_sleep = AsyncMock()

        # Configure the session to raise ClientResponseError on the first call
        mock_session.get.side_effect = [
            aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=429,
                message="Too Many Requests",
            ),
            self.mock_response,  # Successful response on the second call
        ]

        # Patch asyncio.sleep
        with patch("asyncio.sleep", mock_sleep):
            # Call the method
            await scraper.scrape(test_url)

        # Assertions
        assert mock_session.get.call_count == 2
        mock_sleep.assert_called_once_with(scraper.retry_delay)

    @pytest.mark.asyncio
    async def test_make_request_retry_on_429(self, scraper, mocker):
        """Test that _make_request retries on 429 status code."""
        # Setup
        test_url = "http://example.com"

        # Create a mock sleep function to track calls
        mock_sleep = mocker.AsyncMock()

        # Create a mock request function that raises an error first, then succeeds
        error_raised = False

        async def mock_request_func(**kwargs):
            nonlocal error_raised
            if not error_raised:
                error_raised = True
                raise aiohttp.ClientResponseError(
                    request_info=mocker.Mock(),
                    history=(),
                    status=429,
                    message="Too Many Requests",
                )
            return "<html><h1>Test Job</h1></html>"

        # Call the method with our injected mocks
        result = await scraper._make_request(
            url=test_url,
            max_retries=3,
            retry_delay=0.1,
            sleep_func=mock_sleep,
            request_func=mock_request_func,
        )

        # Assertions
        assert "<html><h1>Test Job</h1>" in result

        # Verify sleep was called
        mock_sleep.assert_called_once()

        # We know it must have been called twice because it succeeded after the retry

    @pytest.mark.asyncio
    async def test_make_request_retry_on_500(self, scraper, mocker):
        """Test that _make_request retries on 500 status code."""
        # Setup
        test_url = "http://example.com"

        # Create a mock sleep function to track calls
        mock_sleep = mocker.AsyncMock()

        # Track the number of requests made
        request_count = 0

        # Create a mock request function that raises an error first, then succeeds
        async def mock_request_func(**kwargs):
            nonlocal request_count
            request_count += 1
            if request_count == 1:
                raise aiohttp.ClientResponseError(
                    request_info=mocker.Mock(),
                    history=(),
                    status=500,
                    message="Internal Server Error",
                )
            return "<html><h1>Test Job</h1></html>"

        # Call the method with our injected mocks
        result = await scraper._make_request(
            url=test_url,
            max_retries=3,
            retry_delay=0.1,
            sleep_func=mock_sleep,
            request_func=mock_request_func,
        )

        # Assertions
        assert "<html><h1>Test Job</h1>" in result

        # Verify sleep was called
        mock_sleep.assert_called_once()

        # Verify the correct number of requests were made
        assert request_count == 2

    @pytest.mark.asyncio
    async def test_make_request_fails_after_max_retries(self, scraper, mocker):
        """Test that _make_request raises an exception after max retries."""
        # Setup
        test_url = "http://example.com"
        max_retries = 2

        # Create a mock sleep function to track calls
        mock_sleep = mocker.AsyncMock()

        # Track the number of requests made
        request_count = 0

        # Create a mock request function that always raises an error
        async def mock_request_func(**kwargs):
            nonlocal request_count
            request_count += 1
            raise aiohttp.ClientResponseError(
                request_info=mocker.Mock(),
                history=(),
                status=500,
                message="Internal Server Error",
            )

        # Call the method and expect an exception
        with pytest.raises(aiohttp.ClientResponseError):
            await scraper._make_request(
                url=test_url,
                max_retries=max_retries,
                retry_delay=0.1,
                sleep_func=mock_sleep,
                request_func=mock_request_func,
            )

        # Verify sleep was called for each retry
        assert mock_sleep.call_count == max_retries

        # Verify the correct number of requests were made (initial + retries)
        assert request_count == max_retries + 1

    @pytest.mark.asyncio
    async def test_save_results(self, scraper, tmp_path, sample_job_data):
        """Test saving results to a file."""
        test_file = tmp_path / "test_output.json"

        # Setup the mock file object
        mock_file_write = AsyncMock()  # To be used by the mock file's write method
        mock_file_obj = MagicMock()
        mock_file_obj.write = mock_file_write

        # Create a mock async context manager for aiofiles.open
        @asynccontextmanager
        async def mock_aiofiles_open_context(*args, **kwargs):
            yield mock_file_obj

        # Mock aiofiles.open and os.makedirs
        with (
            patch(
                "aiofiles.open", return_value=mock_aiofiles_open_context()
            ) as mock_aioopen,
            patch("os.makedirs") as mock_makedirs,
        ):
            # Call the method
            await scraper.save_results([sample_job_data], str(test_file))

            # Verify directory creation
            mock_makedirs.assert_called_once_with(
                os.path.dirname(os.path.abspath(str(test_file))), exist_ok=True
            )

            # Verify the file was opened in write mode with correct args
            mock_aioopen.assert_called_once_with(str(test_file), "w", encoding="utf-8")

            # Verify write was called with JSON data
            mock_file_write.assert_awaited_once()

            # Get the written content and parse it as JSON
            written_content = mock_file_write.await_args[0][0]
            data = json.loads(written_content)

            # Verify the content
            assert len(data) == 1
            assert data[0]["title"] == sample_job_data["title"]
            assert data[0]["company"] == sample_job_data["company"]

            assert data[0]["title"] == sample_job_data["title"]
            assert data[0]["company"] == sample_job_data["company"]
