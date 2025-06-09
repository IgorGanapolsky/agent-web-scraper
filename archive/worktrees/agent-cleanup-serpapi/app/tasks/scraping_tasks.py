"""
Celery tasks for web scraping operations
"""

from datetime import datetime
from typing import Any

from app.config.logging import get_logger
from app.core.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, name="scrape_reddit_pain_points")
def scrape_reddit_pain_points(self, query: str, max_posts: int = 50) -> dict[str, Any]:
    """
    Background task to scrape Reddit for pain points
    """
    try:
        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 0,
                "total": max_posts,
                "status": f"Starting Reddit scrape for: {query}",
            },
        )

        # Import here to avoid circular imports
        from app.scrapers.reddit_scraper import RedditScraper

        scraper = RedditScraper()

        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 10,
                "total": max_posts,
                "status": "Initializing Reddit API connection",
            },
        )

        # Perform the scraping
        results = scraper.search_pain_points(query, max_posts)

        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 80,
                "total": max_posts,
                "status": "Processing and analyzing results",
            },
        )

        # Store results
        result_data = {
            "task_id": self.request.id,
            "query": query,
            "max_posts": max_posts,
            "results_count": len(results.get("posts", [])),
            "results": results,
            "completed_at": datetime.now().isoformat(),
            "status": "SUCCESS",
        }

        # Final update
        self.update_state(
            state="SUCCESS",
            meta={
                "current": max_posts,
                "total": max_posts,
                "status": "Scraping completed successfully",
                "results": result_data,
            },
        )

        logger.info(f"Reddit scraping task completed: {self.request.id}")
        return result_data

    except Exception as exc:
        logger.error(f"Reddit scraping task failed: {exc}")
        self.update_state(
            state="FAILURE", meta={"error": str(exc), "status": "Task failed"}
        )
        raise


@celery_app.task(bind=True, name="analyze_market_trends")
def analyze_market_trends(self, data: dict[str, Any]) -> dict[str, Any]:
    """
    Background task to analyze market trends from scraped data
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 0,
                "total": 100,
                "status": "Starting market trend analysis",
            },
        )

        # Import AI analysis modules
        from app.utils.analytics import calculate_pain_point_metrics

        # Perform analysis
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 50,
                "total": 100,
                "status": "Calculating pain point metrics",
            },
        )

        metrics = calculate_pain_point_metrics(data)

        result_data = {
            "task_id": self.request.id,
            "analysis_type": "market_trends",
            "metrics": metrics,
            "completed_at": datetime.now().isoformat(),
            "status": "SUCCESS",
        }

        self.update_state(
            state="SUCCESS",
            meta={
                "current": 100,
                "total": 100,
                "status": "Analysis completed successfully",
                "results": result_data,
            },
        )

        return result_data

    except Exception as exc:
        logger.error(f"Market analysis task failed: {exc}")
        self.update_state(
            state="FAILURE", meta={"error": str(exc), "status": "Analysis failed"}
        )
        raise


@celery_app.task(bind=True, name="generate_insight_report")
def generate_insight_report(self, scrape_results: dict[str, Any]) -> dict[str, Any]:
    """
    Background task to generate AI-powered insight reports
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Generating AI insights"},
        )

        # Import AI modules
        from app.core.llm_client import GPT4Client

        gpt4_client = GPT4Client()

        # Generate insights
        self.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Processing with GPT-4"},
        )

        insights = gpt4_client.generate_insight_summary(scrape_results)

        result_data = {
            "task_id": self.request.id,
            "report_type": "ai_insights",
            "insights": insights,
            "completed_at": datetime.now().isoformat(),
            "status": "SUCCESS",
        }

        self.update_state(
            state="SUCCESS",
            meta={
                "current": 100,
                "total": 100,
                "status": "Report generated successfully",
                "results": result_data,
            },
        )

        return result_data

    except Exception as exc:
        logger.error(f"Insight generation task failed: {exc}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "status": "Report generation failed"},
        )
        raise
