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
    Falls back to CSV logging if Google Sheets unavailable.

    Args:
        query: The search query used today
        leads: Number of leads generated
        replies: Number of replies/interactions
        revenue: Revenue generated (usually 0 for tracking purposes)
        top_3: List of top 3 pain points with labels, explanations, and links

    Returns:
        bool: True if successful, False otherwise
    """
    # Try Google Sheets first
    try:
        # Load credentials
        creds_path = os.getenv(
            "GSPREAD_CREDENTIALS_PATH", "secrets/gsheet_service_account.json"
        )

        with open(creds_path) as f:
            creds_json = json.load(f)

        # Check if this is the template file
        if creds_json.get("project_id") == "your-project-id":
            raise ValueError(
                "Using template credentials - need real Google Sheets setup"
            )

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

        logger.info(
            f"Daily metrics logged to Google Sheets: {leads} leads, query: {query}"
        )
        print("✅ Daily metrics row successfully appended to Google Sheet.")
        return True

    except Exception as e:
        logger.warning(f"Google Sheets failed: {e}, falling back to CSV")
        print(f"⚠️  Google Sheets unavailable: {e}")

        # Fallback to CSV logging
        return _append_daily_metrics_csv(query, leads, replies, revenue, top_3)


def _append_daily_metrics_csv(
    query: str, leads: int, replies: int, revenue: float, top_3: list[dict[str, str]]
) -> bool:
    """Fallback CSV logging when Google Sheets unavailable"""

    try:
        import csv
        from pathlib import Path

        # Create data directory
        data_dir = Path("data/metrics")
        data_dir.mkdir(parents=True, exist_ok=True)

        csv_file = data_dir / "reddit_metrics_daily.csv"

        # Check if file exists to determine if we need headers
        write_headers = not csv_file.exists()

        # Prepare row data
        today = datetime.now().strftime("%m/%d/%Y")

        row = [today, query, leads, replies, revenue]

        # Add pain point data (3 pain points x 3 fields each)
        for i in range(3):
            if i < len(top_3):
                pain_point = top_3[i]
                row.extend(
                    [
                        pain_point.get("pain_point_label", ""),
                        pain_point.get("explanation", ""),
                        pain_point.get("gsheet_link", ""),
                    ]
                )
            else:
                row.extend(["", "", ""])  # Empty fields for missing pain points

        # Write to CSV
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write headers if new file
            if write_headers:
                headers = [
                    "Date",
                    "Query",
                    "Leads",
                    "Replies",
                    "Revenue",
                    "Pain_Point_1_Label",
                    "Pain_Point_1_Explanation",
                    "Pain_Point_1_Link",
                    "Pain_Point_2_Label",
                    "Pain_Point_2_Explanation",
                    "Pain_Point_2_Link",
                    "Pain_Point_3_Label",
                    "Pain_Point_3_Explanation",
                    "Pain_Point_3_Link",
                ]
                writer.writerow(headers)

            writer.writerow(row)

        logger.info(f"Daily metrics logged to CSV: {leads} leads, query: {query}")
        print(f"✅ Metrics logged to fallback CSV: {csv_file}")
        return True

    except Exception as csv_error:
        logger.error(f"CSV fallback also failed: {csv_error}")
        print(f"❌ Both Google Sheets and CSV logging failed: {csv_error}")
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
