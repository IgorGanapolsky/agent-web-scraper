"""
Metrics tracking utilities for daily business metrics and pain point analysis.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def append_daily_metrics_row(
    query: str,
    leads: int,
    replies: int,
    revenue: float,
    top_3: list[dict[str, str]],
) -> bool:
    """
    Append a daily metrics row to the Google Sheets tracking spreadsheet.

    Args:
        query: The search query used today
        leads: Number of leads generated
        replies: Number of replies/interactions
        revenue: Revenue generated (usually 0 for tracking purposes)
        top_3: List of top 3 pain points with labels, explanations, and links

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load credentials
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

        # Open the metrics spreadsheet
        spreadsheet = gc.open_by_key("1KJYQCX-cJsEkUPh7GKwigI71CODun504VOdC4NfNLfY")
        worksheet = spreadsheet.sheet1

        # Get today's date in the required format
        today = datetime.today().strftime("%-m/%-d/%Y")  # e.g. 5/29/2025

        # Ensure we have exactly 3 pain points (pad if necessary)
        pain_points = top_3[:3] if len(top_3) >= 3 else top_3
        while len(pain_points) < 3:
            pain_points.append(
                {"pain_point_label": "", "explanation": "", "gsheet_link": ""}
            )

        # Prepare the row data
        row = [
            today,
            query,
            leads,
            replies,
            revenue,
        ]

        # Add pain point data (3 pain points x 3 fields each)
        for pain_point in pain_points:
            row.append(pain_point.get("pain_point_label", ""))
            row.append(pain_point.get("explanation", ""))
            row.append(pain_point.get("gsheet_link", ""))

        # Pad to ensure exactly 14 columns (5 base + 9 pain point fields)
        while len(row) < 14:
            row.append("")

        # Append the row to the spreadsheet
        worksheet.append_row(row)

        logger.info(f"Daily metrics logged: {leads} leads, query: {query}")
        print("✅ Daily metrics row successfully appended to Google Sheet.")

        return True

    except Exception as e:
        logger.error(f"Error appending daily metrics row: {e}")
        print(f"❌ Failed to append daily metrics: {e}")
        return False


def extract_top_pain_points(
    results: list[dict[str, Any]], max_points: int = 3
) -> list[dict[str, str]]:
    """
    Extract top pain points from Reddit scraper results.

    Args:
        results: List of Reddit scraper results with summaries
        max_points: Maximum number of pain points to extract

    Returns:
        List of pain point dictionaries with label, explanation, and link
    """
    pain_points = []

    for result in results[:max_points]:
        if result.get("summary") and result["summary"] != "Error generating summary":
            pain_point = {
                "pain_point_label": (
                    result["post"]["title"][:50] + "..."
                    if len(result["post"]["title"]) > 50
                    else result["post"]["title"]
                ),
                "explanation": (
                    result["summary"][:100] + "..."
                    if len(result["summary"]) > 100
                    else result["summary"]
                ),
                "gsheet_link": result["post"]["url"],
            }
            pain_points.append(pain_point)

    return pain_points
