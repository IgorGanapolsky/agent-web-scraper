import os

import praw
from dotenv import load_dotenv

load_dotenv()


class RedditClient:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
        )

    def fetch_comments(self, post_url: str, limit: int = 10) -> list[str]:
        try:
            submission = self.reddit.submission(url=post_url)
            submission.comments.replace_more(limit=0)
            comments = [c.body for c in submission.comments.list()[:limit]]
            return comments
        except Exception as e:
            print(f"❌ Reddit API error: {e}")
            return []
