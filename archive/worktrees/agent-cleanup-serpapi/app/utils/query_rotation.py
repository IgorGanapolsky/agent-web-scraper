"""
Query rotation system for daily variety in Reddit scraping.
"""

from datetime import datetime


def get_daily_query() -> str:
    """
    Get today's search query based on date rotation.

    Returns:
        str: Today's search query
    """
    queries = [
        "AI tools for business automation",
        "SaaS startup pain points",
        "small business software problems",
        "productivity tools frustrations",
        "marketing automation challenges",
        "customer support software issues",
        "project management tool complaints",
        "accounting software problems",
        "CRM system frustrations",
        "email marketing pain points",
        "social media management struggles",
        "e-commerce platform issues",
        "workflow automation problems",
        "data analytics tool complaints",
        "team collaboration software issues",
    ]

    # Use day of year to rotate through queries
    day_of_year = datetime.now().timetuple().tm_yday
    query_index = day_of_year % len(queries)

    return queries[query_index]


def get_weekly_queries() -> list[str]:
    """
    Get this week's query rotation schedule.

    Returns:
        List[str]: List of 7 queries for the week
    """
    queries = [
        "AI tools for business automation",
        "SaaS startup pain points",
        "small business software problems",
        "productivity tools frustrations",
        "marketing automation challenges",
        "customer support software issues",
        "project management tool complaints",
    ]

    # Use day of week (0=Monday, 6=Sunday)
    weekday = datetime.now().weekday()

    # Rotate the list to start from today
    rotated_queries = queries[weekday:] + queries[:weekday]

    return rotated_queries


def get_query_analytics() -> dict:
    """
    Get analytics about query rotation.

    Returns:
        dict: Query rotation statistics
    """
    today_query = get_daily_query()
    week_queries = get_weekly_queries()

    return {
        "today_query": today_query,
        "week_schedule": week_queries,
        "total_queries": 15,
        "rotation_method": "day_of_year",
        "current_day": datetime.now().timetuple().tm_yday,
    }
