"""
Enhanced analytics for email reporting and insights.
"""

import time
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any


def performance_monitor(func: Callable) -> Callable:
    """
    Decorator to monitor function performance and execution time.

    Args:
        func: Function to monitor

    Returns:
        Wrapped function with performance monitoring
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            print(f"⚡ {func.__name__} completed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {func.__name__} failed after {execution_time:.2f}s: {e}")
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            print(f"⚡ {func.__name__} completed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {func.__name__} failed after {execution_time:.2f}s: {e}")
            raise

    # Return appropriate wrapper based on function type
    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def calculate_pain_point_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate comprehensive metrics from Reddit scraping results.

    Args:
        results: List of Reddit scraping results

    Returns:
        dict: Comprehensive analytics
    """
    total_posts = len(results)
    total_comments = sum(len(r["post"].get("comments", [])) for r in results)

    # Analyze pain point categories
    pain_point_categories = {}
    sentiment_scores = {"high": 0, "medium": 0, "low": 0}

    for result in results:
        if result["post"].get("pain_point_summaries"):
            for pain_point in result["post"]["pain_point_summaries"]:
                if isinstance(pain_point, dict) and pain_point.get("pain_point_label"):
                    label = pain_point["pain_point_label"].lower()

                    # Categorize pain points
                    if any(
                        word in label for word in ["ai", "automation", "artificial"]
                    ):
                        category = "AI & Automation"
                    elif any(
                        word in label
                        for word in ["cost", "price", "expensive", "budget"]
                    ):
                        category = "Cost & Pricing"
                    elif any(
                        word in label for word in ["integration", "api", "connect"]
                    ):
                        category = "Integration Issues"
                    elif any(word in label for word in ["support", "help", "customer"]):
                        category = "Support & Service"
                    elif any(
                        word in label for word in ["usability", "complex", "difficult"]
                    ):
                        category = "Usability Issues"
                    else:
                        category = "Other"

                    pain_point_categories[category] = (
                        pain_point_categories.get(category, 0) + 1
                    )

                    # Simple sentiment analysis based on keywords
                    explanation = pain_point.get("explanation", "").lower()
                    if any(
                        word in explanation
                        for word in ["terrible", "awful", "hate", "frustrated"]
                    ):
                        sentiment_scores["high"] += 1
                    elif any(
                        word in explanation for word in ["annoying", "problem", "issue"]
                    ):
                        sentiment_scores["medium"] += 1
                    else:
                        sentiment_scores["low"] += 1

    return {
        "scraping_metrics": {
            "total_posts_analyzed": total_posts,
            "total_comments_processed": total_comments,
            "avg_comments_per_post": (
                round(total_comments / total_posts, 1) if total_posts > 0 else 0
            ),
            "scraping_timestamp": datetime.now().isoformat(),
        },
        "pain_point_categories": pain_point_categories,
        "sentiment_distribution": sentiment_scores,
        "top_category": (
            max(pain_point_categories.items(), key=lambda x: x[1])[0]
            if pain_point_categories
            else "None"
        ),
        "total_pain_points": sum(pain_point_categories.values()),
    }


def generate_trend_analysis(current_metrics: dict[str, Any]) -> str:
    """
    Generate trend analysis text for email reports.

    Args:
        current_metrics: Today's metrics

    Returns:
        str: Formatted trend analysis
    """
    analysis = []

    # Posts analysis
    total_posts = current_metrics["scraping_metrics"]["total_posts_analyzed"]
    total_comments = current_metrics["scraping_metrics"]["total_comments_processed"]

    analysis.append(
        f"📊 **Volume**: Analyzed {total_posts} Reddit posts with {total_comments} comments"
    )

    # Category analysis
    if current_metrics["pain_point_categories"]:
        top_category = current_metrics["top_category"]
        analysis.append(f"🎯 **Top Issue Category**: {top_category}")

    # Sentiment analysis
    sentiment = current_metrics["sentiment_distribution"]
    high_sentiment = sentiment.get("high", 0)
    if high_sentiment > 0:
        analysis.append(
            f"🔥 **High Frustration**: {high_sentiment} severe pain points detected"
        )

    return "\n".join(analysis)


def format_enhanced_email_body(
    top_3: list[dict[str, str]], analytics: dict[str, Any], query: str
) -> str:
    """
    Format enhanced email body with analytics and insights.

    Args:
        top_3: Top 3 pain points
        analytics: Calculated analytics
        query: Search query used

    Returns:
        str: Formatted email body
    """
    today = datetime.now().strftime("%B %d, %Y")

    # Header
    email_body = f"""📈 Daily SaaS Pain Point Report - {today}

🔍 **Search Query**: "{query}"

{generate_trend_analysis(analytics)}

🔥 **Top 3 Pain Points**:
"""

    # Pain points
    for i, point in enumerate(top_3, 1):
        if point.get("pain_point_label"):
            email_body += f"""
{i}. **{point['pain_point_label']}**
   {point.get('explanation', 'No explanation available')}
   📊 Link: {point.get('gsheet_link', 'No link available')}
"""

    # Footer with categories
    if analytics["pain_point_categories"]:
        email_body += """
📋 **Pain Point Categories**:
"""
        for category, count in sorted(
            analytics["pain_point_categories"].items(), key=lambda x: x[1], reverse=True
        ):
            email_body += f"   • {category}: {count}\n"

    # Next query preview
    email_body += """
🔄 **Tomorrow's Focus**: Check back for insights on different market segments

📈 **View Full Dashboard**: https://docs.google.com/spreadsheets/d/1KJYQCX-cJsEkUPh7GKwigI71CODun504VOdC4NfNLfY/edit
"""

    return email_body
