#!/usr/bin/env python3
"""
FALLBACK: Local CSV logging for Reddit metrics when Google Sheets unavailable
"""

import csv
from datetime import datetime
from pathlib import Path


def append_daily_metrics_csv(query, leads, replies, revenue, top_3):
    """Log daily metrics to local CSV file as fallback"""

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

    print(f"✅ Metrics logged to: {csv_file}")
    return True


# Test with mock data for June 5
if __name__ == "__main__":
    mock_top_3 = [
        {
            "pain_point_label": "Manual customer onboarding workflows",
            "explanation": "Teams spend 4+ hours manually onboarding each customer",
            "gsheet_link": "https://reddit.com/r/saas/example1",
        },
        {
            "pain_point_label": "Lack of automated email sequences",
            "explanation": "Sales teams manually send follow-up emails, missing prospects",
            "gsheet_link": "https://reddit.com/r/entrepreneur/example2",
        },
        {
            "pain_point_label": "No unified customer data dashboard",
            "explanation": "Customer data scattered across multiple tools",
            "gsheet_link": "https://reddit.com/r/startups/example3",
        },
    ]

    append_daily_metrics_csv(
        query="SaaS automation pain points",
        leads=12,
        replies=47,
        revenue=0.0,
        top_3=mock_top_3,
    )
    print("🎯 June 5 mock data logged successfully!")
