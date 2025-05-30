"""
Weekly pain point clustering and lead magnet generation using Gemini Ultra.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

import gspread
import pandas as pd
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

from app.core.gemini_client import GeminiClient

load_dotenv()

logger = logging.getLogger(__name__)


class WeeklyAnalytics:
    """Generate weekly insights and lead magnets from accumulated data."""

    def __init__(self):
        """Initialize weekly analytics with Google Sheets and Gemini clients."""
        self.gemini = GeminiClient()
        self._init_google_sheets()

    def _init_google_sheets(self):
        """Initialize Google Sheets client."""
        try:
            creds_path = os.getenv(
                "GSPREAD_CREDENTIALS_PATH", "secrets/gsheet_service_account.json"
            )

            with open(creds_path) as f:
                creds_json = json.load(f)

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            credentials = Credentials.from_service_account_info(
                creds_json, scopes=scopes
            )
            self.gc = gspread.authorize(credentials)

            # Open the metrics spreadsheet
            self.spreadsheet = self.gc.open_by_key(
                "1KJYQCX-cJsEkUPh7GKwigI71CODun504VOdC4NfNLfY"
            )

            # Try to find the correct worksheet - use "Reddit Metrics Daily"
            try:
                self.metrics_sheet = self.spreadsheet.worksheet("Reddit Metrics Daily")
            except gspread.exceptions.WorksheetNotFound:
                logger.warning(
                    "'Reddit Metrics Daily' worksheet not found, using first sheet"
                )
                self.metrics_sheet = self.spreadsheet.sheet1

            logger.info("Google Sheets client initialized for weekly analytics")

        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            raise

    def get_weekly_data(self, weeks_back: int = 1) -> pd.DataFrame:
        """
        Fetch last N weeks of data from Google Sheets.

        Args:
            weeks_back: Number of weeks to look back (default: 1)

        Returns:
            DataFrame with weekly data
        """
        try:
            # Get all data from the metrics sheet
            all_data = self.metrics_sheet.get_all_records()

            if not all_data:
                logger.warning("No data found in metrics sheet")
                return pd.DataFrame()

            df = pd.DataFrame(all_data)

            # Debug: Print available columns
            logger.info(f"Available columns: {list(df.columns)}")

            # Find date column - try common variations
            date_column = None
            for col in df.columns:
                if any(word in col.lower() for word in ["date", "time", "created"]):
                    date_column = col
                    break

            if not date_column and len(df.columns) > 0:
                # Use first column as date if no date column found
                date_column = df.columns[0]
                logger.warning(
                    f"No date column found, using first column: {date_column}"
                )

            if date_column:
                # Convert date column to datetime
                df["Date"] = pd.to_datetime(df[date_column], errors="coerce")

                # Filter to last N weeks
                cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
                weekly_df = df[df["Date"].notna() & (df["Date"] >= cutoff_date)]
            else:
                # If no date column, return all data
                logger.warning("No date column found, returning all data")
                weekly_df = df

            logger.info(
                f"Retrieved {len(weekly_df)} records from last {weeks_back} weeks"
            )
            return weekly_df

        except Exception as e:
            logger.error(f"Error fetching weekly data: {e}")
            return pd.DataFrame()

    def cluster_pain_points(self, weekly_data: pd.DataFrame) -> dict[str, Any]:
        """
        Use Gemini to cluster and analyze pain points from weekly data.

        Args:
            weekly_data: DataFrame with weekly pain point data

        Returns:
            Dict with clustered insights
        """
        if weekly_data.empty:
            return {"error": "No data to analyze"}

        # Extract all pain points from the data
        all_pain_points = []

        for _, row in weekly_data.iterrows():
            try:
                # Parse pain points from JSON columns
                for i in range(1, 4):  # Top 3 pain points
                    pain_point_col = f"Pain Point {i}"
                    explanation_col = f"Explanation {i}"

                    if row.get(pain_point_col):
                        all_pain_points.append(
                            {
                                "date": row["Date"].strftime("%Y-%m-%d"),
                                "query": row.get("Query", ""),
                                "pain_point": row[pain_point_col],
                                "explanation": row.get(explanation_col, ""),
                            }
                        )
            except Exception as e:
                logger.warning(f"Error parsing row data: {e}")
                continue

        # Create content for Gemini analysis
        pain_points_content = "\n\n".join(
            [
                f"Date: {pp['date']}\nQuery: {pp['query']}\nPain Point: {pp['pain_point']}\nExplanation: {pp['explanation']}"
                for pp in all_pain_points
            ]
        )

        # Use Gemini to cluster and analyze
        clustering_prompt = """
You are a senior market research analyst tasked with identifying the most significant business opportunities from SaaS pain point data.

TASK: Analyze the following pain points collected over the past week and create strategic business clusters.

DELIVERABLES:
1. Identify 3-5 major pain point CLUSTERS (themes that appear repeatedly)
2. For each cluster, provide:
   - cluster_name: Catchy, business-focused name (max 5 words)
   - market_size: Estimated market impact (Small/Medium/Large/Massive)
   - urgency: How urgent is this problem (Low/Medium/High/Critical)
   - solution_complexity: How hard to solve (Simple/Moderate/Complex/Advanced)
   - revenue_potential: Potential revenue opportunity (Low/Medium/High/Massive)
   - key_pain_points: List of specific pain points in this cluster
   - target_personas: Who suffers from this most
   - existing_solutions: Current solutions and their gaps
   - opportunity_summary: 2-3 sentence opportunity description

3. Rank clusters by business opportunity score (combining market size, urgency, revenue potential)

Return as JSON with 'clusters' array and 'executive_summary' string.
"""

        return self.gemini.generate_json_summary(clustering_prompt, pain_points_content)

    def generate_lead_magnet_content(self, clusters: dict[str, Any]) -> dict[str, str]:
        """
        Generate lead magnet content based on pain point clusters.

        Args:
            clusters: Clustered pain point analysis

        Returns:
            Dict with lead magnet content sections
        """
        if "clusters" not in clusters:
            return {"error": "No clusters found for lead magnet generation"}

        current_date = datetime.now()
        quarter = f"Q{((current_date.month - 1) // 3) + 1}"
        year = current_date.year

        lead_magnet_prompt = f"""
You are a content marketing expert creating a premium lead magnet report.

Based on the pain point clusters provided, create a comprehensive business report:

REPORT SPECS:
- Title: "The {quarter} {year} SaaS Pain Point Report: [Compelling Subtitle]"
- Target: SaaS founders, product managers, and entrepreneurs
- Length: 10-12 pages of actionable content
- Tone: Professional, data-driven, actionable

SECTIONS TO CREATE:
1. executive_summary (2-3 paragraphs)
2. key_findings (3-5 bullet points with data)
3. market_opportunities (detailed analysis of top 3 clusters)
4. actionable_insights (specific steps readers can take)
5. industry_trends (what this means for the future)
6. next_steps (clear CTA and recommendations)
7. about_section (brief description of research methodology)

REQUIREMENTS:
- Include specific data points and percentages where relevant
- Make it scannable with headers, bullets, and key takeaways
- Include at least 3 "Pro Tips" or "Key Insight" callout boxes
- End with clear next steps and value proposition
- Write like a McKinsey consultant but accessible to startup founders

Format as JSON with each section as a key.
"""

        clusters_content = json.dumps(clusters, indent=2)
        return self.gemini.generate_json_summary(lead_magnet_prompt, clusters_content)

    def generate_weekly_report(self, weeks_back: int = 1) -> dict[str, Any]:
        """
        Generate complete weekly analysis and lead magnet.

        Args:
            weeks_back: Number of weeks to analyze

        Returns:
            Dict with complete analysis and content
        """
        logger.info(f"Generating weekly report for last {weeks_back} weeks")

        # Step 1: Get weekly data
        weekly_data = self.get_weekly_data(weeks_back)
        if weekly_data.empty:
            return {"error": "No data available for analysis"}

        # Step 2: Cluster pain points
        clusters = self.cluster_pain_points(weekly_data)
        if "error" in clusters:
            return clusters

        # Step 3: Generate lead magnet content
        lead_magnet = self.generate_lead_magnet_content(clusters)
        if "error" in lead_magnet:
            return lead_magnet

        # Step 4: Create comprehensive report
        report = {
            "generation_date": datetime.now().isoformat(),
            "analysis_period": f"Last {weeks_back} weeks",
            "data_points": len(weekly_data),
            "pain_point_clusters": clusters,
            "lead_magnet_content": lead_magnet,
            "metadata": {
                "total_queries_analyzed": (
                    weekly_data["Query"].nunique()
                    if "Query" in weekly_data.columns
                    else 0
                ),
                "date_range": {
                    "start": (
                        weekly_data["Date"].min().isoformat()
                        if not weekly_data.empty
                        else None
                    ),
                    "end": (
                        weekly_data["Date"].max().isoformat()
                        if not weekly_data.empty
                        else None
                    ),
                },
            },
        }

        logger.info("Weekly report generated successfully")
        return report

    def _flatten_field(self, val: Any) -> str:
        """
        Flatten complex data structures for Google Sheets compatibility.

        Args:
            val: Value to flatten

        Returns:
            str: Flattened string representation
        """
        if isinstance(val, list):
            return "; ".join(str(item) for item in val)
        if isinstance(val, dict):
            return str(val)
        return str(val)

    def save_report_to_sheets(self, report: dict[str, Any]) -> bool:
        """
        Save the weekly report to a new Google Sheets tab.

        Args:
            report: Generated weekly report

        Returns:
            bool: Success status
        """
        try:
            # Create new worksheet for this week's report
            report_date = datetime.now().strftime("%Y-%m-%d")
            worksheet_name = f"Weekly_Report_{report_date}"

            # Check if worksheet already exists, delete if it does
            try:
                existing_sheet = self.spreadsheet.worksheet(worksheet_name)
                self.spreadsheet.del_worksheet(existing_sheet)
            except gspread.exceptions.WorksheetNotFound:
                pass  # Sheet doesn't exist, that's fine

            # Create new worksheet
            new_sheet = self.spreadsheet.add_worksheet(
                title=worksheet_name, rows=100, cols=10
            )

            # Format the report for sheets
            report_rows = [
                ["Weekly SaaS Pain Point Analysis", ""],
                ["Generated", self._flatten_field(report["generation_date"])],
                ["Analysis Period", self._flatten_field(report["analysis_period"])],
                ["Data Points", self._flatten_field(report["data_points"])],
                ["", ""],
                ["EXECUTIVE SUMMARY", ""],
            ]

            # Add lead magnet content
            if "lead_magnet_content" in report and isinstance(
                report["lead_magnet_content"], dict
            ):
                for section, content in report["lead_magnet_content"].items():
                    report_rows.extend(
                        [
                            [section.upper().replace("_", " "), ""],
                            [self._flatten_field(content), ""],
                            ["", ""],
                        ]
                    )

            # Add to sheet
            new_sheet.update(report_rows)

            logger.info(f"Report saved to Google Sheets: {worksheet_name}")
            return True

        except Exception as e:
            logger.error(f"Error saving report to sheets: {e}")
            return False


def generate_weekly_lead_magnet() -> dict[str, Any]:
    """
    Main function to generate weekly lead magnet.

    Returns:
        Dict with generated report
    """
    try:
        analytics = WeeklyAnalytics()
        report = analytics.generate_weekly_report(weeks_back=1)

        # Save to Google Sheets
        if "error" not in report:
            analytics.save_report_to_sheets(report)

        return report

    except Exception as e:
        logger.error(f"Error generating weekly lead magnet: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Generate and print weekly report
    report = generate_weekly_lead_magnet()
    print(json.dumps(report, indent=2, default=str))
