"""Unit tests for the Reddit scraper."""
import unittest
from unittest.mock import MagicMock, patch

from reddit_scraper import RedditScraper


class TestRedditScraper(unittest.TestCase):
    """Test suite for the RedditScraper class."""

    @patch("reddit_scraper.SERPAPI_KEY", "test_key")
    @patch("reddit_scraper.OPENAI_API_KEY", "test_key")
    @patch("reddit_scraper.RedditScraper._init_google_sheets")
    def setUp(self, mock_init_sheets):
        """Set up the test environment."""
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


if __name__ == "__main__":
    unittest.main()
