"""
Insights API endpoints for the application.

This module provides API endpoints for retrieving and managing insights data.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/")
async def get_insights():
    """Get all insights.

    Returns:
        dict: A dictionary containing insights data.
    """
    return {"message": "Insights endpoint"}
