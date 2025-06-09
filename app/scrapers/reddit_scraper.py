"""
Reddit Scraper - Searches Reddit for posts related to user pain points,
summarizes key insights, and logs results into a Google Sheets spreadsheet.
"""

import json
import logging
import os
import time
from typing import Any

import serpapi
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from security import safe_requests

from app.core.gemini_client import GeminiClient
from app.core.llm_client import GPT4Client
from app.core.utils.audit import safe_requests
from app.utils.analytics import calculate_pain_point_metrics, format_enhanced_email_body
from app.utils.query_rotation import get_daily_query

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Load environment variables from .env file
load_dotenv()

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

        if not self.serpapi_key:
            raise ValueError("SERPAPI_KEY environment variable is not set")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=self.openai_api_key)

        # Google Sheets logging handled by app.utils.top_insights

    # Removed: Fallback Google Sheets initialization
    # All spreadsheet logging now handled by app.utils.top_insights

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
            print(comments)

            # Initialize GPT client
            llm = GPT4Client()

            # Compose summarization prompt
            combined_comments = "\n\n".join(comments)
            prompt = f"""
You are an expert SaaS market researcher analyzing Reddit discussions to identify business pain points and opportunities.

CONTEXT: Analyzing discussions about "{self.search_term}" to find actionable business insights.

TASK: Extract the 3 most significant pain points from this Reddit discussion. Focus on:
- Business problems that could be solved with software/services
- Frustrations that indicate market gaps
- Workflow inefficiencies mentioned by users
- Cost/time wasters that businesses face

For each pain point, provide:
- pain_point_label: Concise business problem (max 8 words)
- explanation: Why this is painful and what it costs businesses (2-3 sentences)
- gsheet_link: Leave empty for now

PRIORITIZE pain points that:
✅ Affect multiple users/businesses
✅ Have clear business impact (time, money, efficiency)
✅ Could be solved with technology/services
✅ Show strong emotional language (frustration, complaints)

AVOID generic complaints or one-off issues.

Respond in JSON array format:
[
  {{
    "pain_point_label": "Short business problem description",
    "explanation": "Why this costs businesses time/money and the impact on operations...",
    "gsheet_link": ""
  }},
  ...
]

Reddit Comments:
\"\"\"
{combined_comments}
\"\"\"
"""

            # Try GPT-4 first
            try:
                top_3 = llm.simple_json(prompt)
                print("🔍 GPT-4 extracted top_3 pain points:")
                print(json.dumps(top_3, indent=2))

                # Validate GPT response
                if not isinstance(top_3, list) or len(top_3) == 0:
                    raise ValueError("Invalid GPT response format")

            except Exception as gpt_error:
                print(f"⚠️ GPT-4 failed: {gpt_error}, trying Gemini...")

                # Fallback to Gemini
                try:
                    gemini = GeminiClient()
                    top_3 = gemini.summarize_reddit_thread(comments, self.search_term)
                    print("🔍 Gemini extracted top_3 pain points:")
                    print(json.dumps(top_3, indent=2))

                    if not top_3:
                        raise ValueError("No insights from Gemini")

                except Exception as gemini_error:
                    print(f"⚠️ Gemini also failed: {gemini_error}")
                    top_3 = []

            # Get post title from URL or use a fallback
            post_title = (
                url.split("/")[-2].replace("_", " ").title()
                if "/" in url
                else "Reddit Post"
            )

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
                response = safe_requests.get(url, headers=headers, timeout=30)
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

    # Removed: Fallback log_to_spreadsheet method
    # All spreadsheet logging now handled by app.utils.top_insights

    def run(self) -> list[dict[str, Any]]:
        """
        Run the Reddit scraper pipeline.

        Returns:
            List of dictionaries containing post data and summaries
        """
        results = []
        all_pain_points = []  # Accumulate pain points from all posts

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

            # Step 4: Spreadsheet logging handled by top_insights module

            # Add to results
            results.append({"post": post_data, "summary": summary})

            # Accumulate pain points from this post
            if post_data.get("pain_point_summaries"):
                summary_data = post_data["pain_point_summaries"]
                if not isinstance(summary_data, list):
                    print(f"⚠️ Unexpected LLM format: {summary_data}")
                    continue
                all_pain_points.extend(summary_data)

        # Step 5: Log daily metrics with accumulated pain points from all posts
        try:
            from app.utils.top_insights import append_daily_metrics_row

            # Select final top 3 from all posts
            top_3 = (
                all_pain_points[:3] if len(all_pain_points) >= 3 else all_pain_points
            )

            # Pad if fewer than 3 pain points
            while len(top_3) < 3:
                top_3.append(
                    {"pain_point_label": "", "explanation": "", "gsheet_link": ""}
                )

            # Log final metrics only if we have content
            if top_3 and any(point.get("pain_point_label") for point in top_3):
                append_daily_metrics_row(
                    query=self.search_term,
                    leads=len(results),
                    replies=sum(len(r["post"].get("comments", [])) for r in results),
                    revenue=0,
                    top_3=top_3,
                )

                print(f"📊 Final top_3 pain points from {len(results)} posts:")
                print(json.dumps(top_3, indent=2))
            else:
                print("❌ Skipping daily metrics append — no top_3 insights extracted.")

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
        default=get_daily_query(),
        help="Search term to look for on Reddit (defaults to daily rotation)",
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

        # Send enhanced analytics email digest
        try:
            from app.utils.email_utils import send_email
            from app.utils.top_insights import extract_top_pain_points

            # Extract top 3 pain points for email
            top_3 = extract_top_pain_points(results, max_points=3)

            # Calculate comprehensive analytics
            analytics = calculate_pain_point_metrics(results)

            # Generate enhanced email body with analytics
            enhanced_digest = format_enhanced_email_body(
                top_3, analytics, args.search_term
            )

            send_email(
                to="support@saasgrowthdispatch.com",
                subject=f"📈 Daily SaaS Insights: {analytics['top_category']} Trends",
                body=enhanced_digest,
            )
        except Exception as e:
            logger.error(f"Error sending enhanced analytics email: {e}")

    except Exception as e:
        logger.error(f"Error running Reddit scraper: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
