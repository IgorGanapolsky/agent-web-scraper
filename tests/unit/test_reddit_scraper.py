"""Unit tests for the Reddit scraper."""
import unittest
from unittest.mock import MagicMock, patch

import gspread

from reddit_scraper import RedditScraper, main


class TestRedditScraper(unittest.TestCase):
    """Test suite for the RedditScraper class."""

    @patch("reddit_scraper.SERPAPI_KEY", "test_key")
    @patch("reddit_scraper.OPENAI_API_KEY", "test_key")
    @patch("reddit_scraper.SPREADSHEET_NAME", "test_spreadsheet")
    @patch("reddit_scraper.OpenAI")
    @patch("reddit_scraper.RedditScraper._init_google_sheets")
    def setUp(self, mock_init_sheets, mock_openai):
        """Set up the test environment."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Test summary of pain points"
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        self.scraper = RedditScraper("test search", max_results=2)
        mock_init_sheets.assert_called_once()

    @patch("reddit_scraper.GoogleSearch")
    def test_search_reddit_urls(self, mock_google_search):
        """Test searching for Reddit URLs."""
        # Mock the GoogleSearch response
        mock_instance = MagicMock()
        mock_instance.get_dict.return_value = {
            "organic_results": [
                {
                    "title": "Test Reddit Post",
                    "link": "https://www.reddit.com/r/test/comments/123/test_post",
                },
                {"title": "Not a Reddit Post", "link": "https://example.com"},
            ]
        }
        mock_google_search.return_value = mock_instance

        # Call the method
        results = self.scraper.search_reddit_urls()

        # Verify the results
        assert len(results) == 1
        assert results[0]["title"] == "Test Reddit Post"
        assert (
            results[0]["url"] == "https://www.reddit.com/r/test/comments/123/test_post"
        )

    @patch("reddit_scraper.requests.get")
    def test_scrape_reddit_post(self, mock_get):
        """Test scraping a Reddit post."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <head><title>Test</title></head>
            <body>
                <h1>Test Reddit Post</h1>
                <div class="Comment">Test comment 1</div>
                <div class="Comment">Test comment 2</div>
                <div class="Comment">short</div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        # Call the method
        result = self.scraper.scrape_reddit_post(
            "https://www.reddit.com/r/test/comments/123/test_post"
        )

        # Verify the results
        assert result["title"] == "Test Reddit Post"
        assert len(result["comments"]) == 2
        assert "Test comment" in result["comments"][0]

    @patch("reddit_scraper.OpenAI")
    def test_summarize_pain_points(self, mock_openai):
        """Test summarizing pain points."""
        # Mock the OpenAI response
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "Test summary of pain points"
        mock_client.chat.completions.create.return_value = mock_completion
        self.scraper.openai_client = mock_client

        # Call the method
        post_data = {
            "title": "Test Post",
            "url": "https://example.com",
            "comments": ["This is a test comment", "This is another test comment"],
        }
        result = self.scraper.summarize_pain_points(post_data)

        # Verify the results
        assert result == "Test summary of pain points"
        mock_client.chat.completions.create.assert_called_once()

    def test_summarize_pain_points_no_comments(self):
        """Test summarizing pain points with no comments."""
        # Call the method
        post_data = {"title": "Test Post", "url": "https://example.com", "comments": []}
        result = self.scraper.summarize_pain_points(post_data)

        # Verify the results
        assert result == "No comments found to analyze"

    @patch("reddit_scraper.SERPAPI_KEY", "")
    @patch("reddit_scraper.OPENAI_API_KEY", "test_key")
    @patch("reddit_scraper.SPREADSHEET_NAME", "test_spreadsheet")
    def test_init_missing_serpapi_key(self):
        """Test initialization with missing SERPAPI_KEY."""
        with self.assertRaises(ValueError) as context:
            RedditScraper("test search")
        assert "SERPAPI_KEY environment variable is not set" in str(context.exception)

    @patch("reddit_scraper.SERPAPI_KEY", "test_key")
    @patch("reddit_scraper.OPENAI_API_KEY", "")
    @patch("reddit_scraper.SPREADSHEET_NAME", "test_spreadsheet")
    def test_init_missing_openai_key(self):
        """Test initialization with missing OPENAI_API_KEY."""
        with self.assertRaises(ValueError) as context:
            RedditScraper("test search")
        assert "OPENAI_API_KEY environment variable is not set" in str(
            context.exception
        )

    @patch("reddit_scraper.SERPAPI_KEY", "test_key")
    @patch("reddit_scraper.OPENAI_API_KEY", "test_key")
    @patch("reddit_scraper.SPREADSHEET_NAME", "test_spreadsheet")
    @patch("reddit_scraper.OpenAI")
    @patch("os.path.exists")
    def test_init_google_sheets_no_service_account(self, mock_exists, mock_openai):
        """Test Google Sheets initialization without service account file."""
        mock_exists.return_value = False
        scraper = RedditScraper("test search")
        assert scraper.sheets_client is None

    @patch("reddit_scraper.SERPAPI_KEY", "test_key")
    @patch("reddit_scraper.OPENAI_API_KEY", "test_key")
    @patch("reddit_scraper.SPREADSHEET_NAME", "test_spreadsheet")
    @patch("reddit_scraper.OpenAI")
    @patch("os.path.exists")
    @patch("reddit_scraper.ServiceAccountCredentials.from_json_keyfile_name")
    @patch("reddit_scraper.gspread.authorize")
    def test_init_google_sheets_success(
        self, mock_gspread, mock_creds, mock_exists, mock_openai
    ):
        """Test successful Google Sheets initialization."""
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_worksheet.row_values.return_value = []
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_client.open.return_value = mock_spreadsheet
        mock_gspread.return_value = mock_client

        scraper = RedditScraper("test search")
        assert scraper.sheets_client == mock_client
        mock_worksheet.append_row.assert_called_once()

    @patch("reddit_scraper.SERPAPI_KEY", "test_key")
    @patch("reddit_scraper.OPENAI_API_KEY", "test_key")
    @patch("reddit_scraper.SPREADSHEET_NAME", "test_spreadsheet")
    @patch("reddit_scraper.OpenAI")
    @patch("os.path.exists")
    @patch("reddit_scraper.ServiceAccountCredentials.from_json_keyfile_name")
    @patch("reddit_scraper.gspread.authorize")
    def test_init_google_sheets_create_new_spreadsheet(
        self, mock_gspread, mock_creds, mock_exists, mock_openai
    ):
        """Test Google Sheets initialization when spreadsheet doesn't exist."""
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_client.open.side_effect = gspread.exceptions.SpreadsheetNotFound
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_client.create.return_value = mock_spreadsheet
        mock_gspread.return_value = mock_client

        scraper = RedditScraper("test search")
        assert scraper.sheets_client == mock_client
        mock_client.create.assert_called_once()
        mock_worksheet.append_row.assert_called_once()

    @patch("reddit_scraper.SERPAPI_KEY", "test_key")
    @patch("reddit_scraper.OPENAI_API_KEY", "test_key")
    @patch("reddit_scraper.SPREADSHEET_NAME", "test_spreadsheet")
    @patch("reddit_scraper.OpenAI")
    @patch("os.path.exists")
    @patch("reddit_scraper.ServiceAccountCredentials.from_json_keyfile_name")
    def test_init_google_sheets_exception(self, mock_creds, mock_exists, mock_openai):
        """Test Google Sheets initialization with exception."""
        mock_exists.return_value = True
        mock_creds.side_effect = Exception("Test error")

        scraper = RedditScraper("test search")
        assert scraper.sheets_client is None

    @patch("reddit_scraper.GoogleSearch")
    def test_search_reddit_urls_exception(self, mock_google_search):
        """Test search_reddit_urls with exception."""
        mock_google_search.side_effect = Exception("API error")

        results = self.scraper.search_reddit_urls()
        assert results == []

    @patch("reddit_scraper.requests.get")
    def test_scrape_reddit_post_exception(self, mock_get):
        """Test scraping a Reddit post with exception."""
        mock_get.side_effect = Exception("Network error")

        result = self.scraper.scrape_reddit_post("https://example.com")
        assert result["title"] == "Error"
        assert result["comments"] == []

    @patch("reddit_scraper.OpenAI")
    def test_summarize_pain_points_exception(self, mock_openai):
        """Test summarizing pain points with OpenAI exception."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("OpenAI error")
        self.scraper.openai_client = mock_client

        post_data = {
            "title": "Test Post",
            "url": "https://example.com",
            "comments": ["Test comment"],
        }
        result = self.scraper.summarize_pain_points(post_data)
        assert result == "Error generating summary"

    def test_log_to_spreadsheet_no_client(self):
        """Test log_to_spreadsheet with no sheets client."""
        self.scraper.sheets_client = None
        post_data = {"title": "Test", "url": "https://example.com"}
        result = self.scraper.log_to_spreadsheet(post_data, "Test summary")
        assert result is False

    @patch("reddit_scraper.SERPAPI_KEY", "test_key")
    @patch("reddit_scraper.OPENAI_API_KEY", "test_key")
    @patch("reddit_scraper.SPREADSHEET_NAME", "test_spreadsheet")
    @patch("reddit_scraper.OpenAI")
    @patch("reddit_scraper.RedditScraper._init_google_sheets")
    def test_log_to_spreadsheet_success(self, mock_init_sheets, mock_openai):
        """Test successful logging to spreadsheet."""
        scraper = RedditScraper("test search")
        mock_worksheet = MagicMock()
        scraper.worksheet = mock_worksheet
        scraper.sheets_client = MagicMock()

        post_data = {"title": "Test", "url": "https://example.com"}
        result = scraper.log_to_spreadsheet(post_data, "Test summary")
        assert result is True
        mock_worksheet.append_row.assert_called_once()

    @patch("reddit_scraper.SERPAPI_KEY", "test_key")
    @patch("reddit_scraper.OPENAI_API_KEY", "test_key")
    @patch("reddit_scraper.SPREADSHEET_NAME", "test_spreadsheet")
    @patch("reddit_scraper.OpenAI")
    @patch("reddit_scraper.RedditScraper._init_google_sheets")
    def test_log_to_spreadsheet_exception(self, mock_init_sheets, mock_openai):
        """Test logging to spreadsheet with exception."""
        scraper = RedditScraper("test search")
        mock_worksheet = MagicMock()
        mock_worksheet.append_row.side_effect = Exception("Sheets error")
        scraper.worksheet = mock_worksheet
        scraper.sheets_client = MagicMock()

        post_data = {"title": "Test", "url": "https://example.com"}
        result = scraper.log_to_spreadsheet(post_data, "Test summary")
        assert result is False

    @patch("reddit_scraper.RedditScraper.search_reddit_urls")
    @patch("reddit_scraper.RedditScraper.scrape_reddit_post")
    @patch("reddit_scraper.RedditScraper.summarize_pain_points")
    @patch("reddit_scraper.RedditScraper.log_to_spreadsheet")
    @patch("reddit_scraper.time.sleep")
    def test_run_method(
        self, mock_sleep, mock_log, mock_summarize, mock_scrape, mock_search
    ):
        """Test the run method."""
        mock_search.return_value = [{"url": "https://reddit.com/test"}]
        mock_scrape.return_value = {
            "title": "Test",
            "url": "https://reddit.com/test",
            "comments": [],
        }
        mock_summarize.return_value = "Test summary"
        mock_log.return_value = True

        results = self.scraper.run()
        assert len(results) == 1
        assert results[0]["summary"] == "Test summary"
        mock_sleep.assert_called_once_with(2)

    @patch("argparse.ArgumentParser.parse_args")
    @patch("reddit_scraper.RedditScraper")
    def test_main_function_success(self, mock_scraper_class, mock_parse_args):
        """Test main function success."""
        mock_args = MagicMock()
        mock_args.search_term = "test"
        mock_args.max_results = 5
        mock_parse_args.return_value = mock_args

        mock_scraper = MagicMock()
        mock_scraper.run.return_value = [
            {"post": {"title": "Test", "url": "test"}, "summary": "Test"}
        ]
        mock_scraper_class.return_value = mock_scraper

        result = main()
        assert result == 0

    @patch("argparse.ArgumentParser.parse_args")
    @patch("reddit_scraper.RedditScraper")
    def test_main_function_exception(self, mock_scraper_class, mock_parse_args):
        """Test main function with exception."""
        mock_args = MagicMock()
        mock_args.search_term = "test"
        mock_args.max_results = 5
        mock_parse_args.return_value = mock_args

        mock_scraper_class.side_effect = Exception("Test error")

        result = main()
        assert result == 1


if __name__ == "__main__":
    unittest.main()
