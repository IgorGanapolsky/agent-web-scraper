"""
Reddit Scraper - Searches Reddit for posts related to user pain points,
summarizes key insights, and logs results into a Google Sheets spreadsheet.
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any

import gspread
import requests
import serpapi
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI

from app.core.llm_client import GPT4Client
from config import OPENAI_API_KEY, SERPAPI_KEY, SPREADSHEET_NAME

# Load environment variables from .env file
load_dotenv()

creds_path = os.getenv(
    "GSPREAD_CREDENTIALS_PATH", "secrets/gsheet_service_account.json"
)
with open(creds_path) as f:
    creds_json = json.load(f)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
credentials = Credentials.from_service_account_info(creds_json, scopes=scopes)
gc = gspread.authorize(credentials)

# Example: open the metrics sheet
spreadsheet = gc.open_by_key("1KJYQCX-cJsEkUPh7GKwigI71CODun504VOdC4NfNLfY")
worksheet = spreadsheet.sheet1  # defaults to first sheet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("reddit_scraper")


class RedditScraper:
    """
    Scrapes Reddit posts and comments for user pain points and summarizes them.
    """

    def __init__(self, search_term: str, max_results: int = 5):
        """
        Initialize the Reddit scraper.

        Args:
            search_term: The search term to look for on Reddit
            max_results: Maximum number of Reddit posts to analyze
        """
        self.search_term = search_term
        self.max_results = max_results
        self.serpapi_key = SERPAPI_KEY
        self.openai_api_key = OPENAI_API_KEY
        self.spreadsheet_name = SPREADSHEET_NAME

        if not self.serpapi_key:
            raise ValueError("SERPAPI_KEY environment variable is not set")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=self.openai_api_key)

        # Initialize Google Sheets client
        self._init_google_sheets()

    def _init_google_sheets(self):
        """Initialize Google Sheets API client."""
        try:
            # Use credentials from service account file
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]

            # Check if service account file exists
            if not os.path.exists("secrets/service_account.json"):
                logger.warning(
                    "Google Sheets service account file not found. "
                    "Spreadsheet logging disabled."
                )
                self.sheets_client = None
                return

            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                "secrets/service_account.json", scope
            )
            self.sheets_client = gspread.authorize(credentials)

            # Try to open the spreadsheet, create it if it doesn't exist
            try:
                self.spreadsheet = self.sheets_client.open(self.spreadsheet_name)
                self.worksheet = self.spreadsheet.sheet1

                # Check if headers exist, add them if not
                headers = self.worksheet.row_values(1)
                if not headers:
                    self.worksheet.append_row(
                        ["Date", "Search Term", "Post Title", "URL", "Summary"]
                    )

            except gspread.exceptions.SpreadsheetNotFound:
                logger.info(f"Creating new spreadsheet: {self.spreadsheet_name}")
                self.spreadsheet = self.sheets_client.create(self.spreadsheet_name)
                self.worksheet = self.spreadsheet.sheet1
                self.worksheet.append_row(
                    ["Date", "Search Term", "Post Title", "URL", "Summary"]
                )

        except Exception as e:
            logger.error(f"Error initializing Google Sheets: {e}")
            self.sheets_client = None

    def search_reddit_urls(self) -> list[dict[str, str]]:
        """
        Search for Reddit URLs using SerpAPI.

        Returns:
            List of dictionaries containing Reddit post URLs and titles
        """
        logger.info(f"Searching for Reddit posts about: {self.search_term}")

        search_params = {
            "q": f"{self.search_term} site:reddit.com",
            "api_key": self.serpapi_key,
            "engine": "google",
            "num": self.max_results,
        }

        try:
            results = serpapi.search(search_params)

            reddit_posts = []
            if "organic_results" in results:
                for result in results["organic_results"]:
                    if (
                        "reddit.com/r/" in result["link"]
                        and "/comments/" in result["link"]
                    ):
                        reddit_posts.append(
                            {"title": result["title"], "url": result["link"]}
                        )

            logger.info(f"Found {len(reddit_posts)} Reddit posts")
            return reddit_posts

        except Exception as e:
            logger.error(f"Error searching Reddit URLs: {e}")
            return []

    def scrape_reddit_post(self, url: str) -> dict[str, Any]:
        """
        Scrape a Reddit post and its comments using Reddit API.

        Args:
            url: URL of the Reddit post

        Returns:
            Dictionary containing post title, content, and comments with GPT-4 analysis
        """
        logger.info(f"Scraping Reddit post: {url}")

        try:
            # Try Reddit API first for better comment extraction
            from app.core.reddit_api import RedditClient

            client = RedditClient()
            comments = client.fetch_comments(url, limit=10)

            # Get post title from URL or use a fallback
            post_title = (
                url.split("/")[-2].replace("_", " ").title()
                if "/" in url
                else "Reddit Post"
            )

            # Process comments with GPT-4 for pain point analysis
            llm = GPT4Client()

            # Join all comments into a single string
            combined_comments = "\n\n".join(comments)

            prompt = f"""
Extract 3 core pain points from the following Reddit discussion. For each, return:
- pain_point_label: A short label
- explanation: What the issue is and why it's painful
- gsheet_link: Leave this empty for now

Respond in JSON array format:
[
  {{
    "pain_point_label": "...",
    "explanation": "...",
    "gsheet_link": ""
  }},
  ...
]

Reddit Comments:
\"\"\"
{combined_comments}
\"\"\"
"""

            top_3 = llm.simple_json(prompt)

            # Print output for debugging
            print("Extracted top_3 pain points:")
            print(json.dumps(top_3, indent=2))

            logger.info(
                f"Extracted {len(top_3) if isinstance(top_3, list) else 'unknown'} pain points from {len(comments)} comments"
            )

            return {
                "title": post_title,
                "url": url,
                "comments": comments,
                "pain_point_summaries": top_3,
            }

        except Exception as e:
            logger.error(
                f"Error scraping Reddit post with API: {e}, falling back to web scraping"
            )

            # Fallback to web scraping if Reddit API fails
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Extract post title
                title_element = soup.find("h1")
                title = (
                    title_element.text.strip() if title_element else "No title found"
                )

                # Extract post content and comments
                comments = []
                comment_elements = soup.find_all(
                    "div", class_=lambda c: c and "Comment" in c
                )

                for comment in comment_elements[:10]:  # Limit to first 10 comments
                    comment_text = comment.get_text(strip=True)
                    if comment_text and len(comment_text) > 50:
                        comments.append(comment_text)

                return {
                    "title": title,
                    "url": url,
                    "comments": comments,
                    "pain_point_summaries": [],
                }

            except Exception as fallback_error:
                logger.error(f"Error with fallback scraping: {fallback_error}")
                return {
                    "title": "Error",
                    "url": url,
                    "comments": [],
                    "pain_point_summaries": [],
                }

    def summarize_pain_points(self, post_data: dict[str, Any]) -> str:
        """
        Use OpenAI to summarize pain points from a Reddit post.

        Args:
            post_data: Dictionary containing post title and comments

        Returns:
            Summary of pain points
        """
        if not post_data["comments"]:
            return "No comments found to analyze"

        # Combine title and comments for analysis
        content = f"Title: {post_data['title']}\n\nComments:\n"
        for i, comment in enumerate(post_data["comments"], 1):
            content += f"{i}. {comment[:500]}...\n\n"  # Truncate long comments

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an analyst identifying user pain points "
                            "from Reddit discussions. Summarize the key pain points, "
                            "frustrations, and needs expressed in this content."
                        ),
                    },
                    {"role": "user", "content": content},
                ],
                max_tokens=300,
                temperature=0.3,
            )

            summary: str = response.choices[0].message.content.strip()
            return summary

        except Exception as e:
            logger.error(f"Error summarizing pain points: {e}")
            return "Error generating summary"

    def log_to_spreadsheet(self, post_data: dict[str, Any], summary: str) -> bool:
        """
        Log the results to Google Sheets.

        Args:
            post_data: Dictionary containing post data
            summary: Summary of pain points

        Returns:
            True if successful, False otherwise
        """
        if not self.sheets_client:
            logger.warning("Google Sheets client not initialized. Skipping logging.")
            return False

        try:
            # Add a new row with the data
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.search_term,
                post_data["title"],
                post_data["url"],
                summary,
            ]

            self.worksheet.append_row(row)
            logger.info(f"Logged results to spreadsheet: {self.spreadsheet_name}")
            return True

        except Exception as e:
            logger.error(f"Error logging to spreadsheet: {e}")
            return False

    def run(self) -> list[dict[str, Any]]:
        """
        Run the Reddit scraper pipeline.

        Returns:
            List of dictionaries containing post data and summaries
        """
        results = []

        # Step 1: Search for Reddit URLs
        reddit_posts = self.search_reddit_urls()

        # Step 2: Scrape each Reddit post
        for post in reddit_posts:
            # Add a delay to avoid rate limiting
            time.sleep(2)

            # Scrape the post
            post_data = self.scrape_reddit_post(post["url"])

            # Step 3: Summarize pain points
            summary = self.summarize_pain_points(post_data)

            # Step 4: Log to spreadsheet
            self.log_to_spreadsheet(post_data, summary)

            # Add to results
            results.append({"post": post_data, "summary": summary})

        # Step 5: Log daily metrics after all posts are scraped
        try:
            from app.utils.top_insights import append_daily_metrics_row

            # Collect all pain points from all scraped posts
            all_pain_points = []
            for result in results:
                if result.get("pain_point_summaries") and isinstance(
                    result["pain_point_summaries"], list
                ):
                    all_pain_points.extend(result["pain_point_summaries"])

            # Take the first 3 pain points (or pad if fewer)
            top_3 = (
                all_pain_points[:3] if len(all_pain_points) >= 3 else all_pain_points
            )
            while len(top_3) < 3:
                top_3.append(
                    {"pain_point_label": "", "explanation": "", "gsheet_link": ""}
                )

            # Log daily metrics
            append_daily_metrics_row(
                query=self.search_term,
                leads=len(results),
                replies=2,  # Example value
                revenue=0,
                top_3=top_3,
            )
        except Exception as e:
            logger.error(f"Error logging daily metrics: {e}")

        return results


def main():
    """Main function to run the Reddit scraper."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Reddit for user pain points")
    parser.add_argument(
        "search_term",
        nargs="?",
        default="AI tools for business automation",
        help="Search term to look for on Reddit",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum number of Reddit posts to analyze",
    )

    args = parser.parse_args()

    try:
        scraper = RedditScraper(args.search_term, args.max_results)
        results = scraper.run()

        # Print results
        print(f"\nAnalyzed {len(results)} Reddit posts about '{args.search_term}':")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['post']['title']}")
            print(f"   URL: {result['post']['url']}")
            print(f"   Summary: {result['summary']}")

        # Send daily email digest
        try:
            from app.utils.email_digest import send_daily_digest_email
            from app.utils.top_insights import extract_top_pain_points

            # Extract top 3 pain points for email
            top_3 = extract_top_pain_points(results, max_points=3)

            send_daily_digest_email(
                query=args.search_term,
                top_3=top_3,
                leads=len(results),
                replies=1,
                revenue=0.00,
            )
        except Exception as e:
            logger.error(f"Error sending daily digest email: {e}")

    except Exception as e:
        logger.error(f"Error running Reddit scraper: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
