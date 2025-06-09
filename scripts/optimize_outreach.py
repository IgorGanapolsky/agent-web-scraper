#!/usr/bin/env python3
"""
Script to optimize outreach strategy based on performance data.
"""

import json
import os
from datetime import datetime


def main():
    """Main function to optimize outreach strategy."""
    print("🧠 AI optimization of outreach strategy...")

    # Create or update performance log
    performance_log = {
        "date": datetime.now().isoformat(),
        "customers": 0,
        "daily_revenue": 0,
    }

    # Load existing performance log if it exists
    if os.path.exists("performance_log.json"):
        with open("performance_log.json") as f:
            logs = json.load(f)
    else:
        logs = []

    # Load and analyze prospects database
    if os.path.exists("prospects_database.json"):
        with open("prospects_database.json") as f:
            prospects = json.load(f)
            performance_log["outreach_sent"] = len(
                [p for p in prospects if p.get("status") == "contacted"]
            )
            performance_log["responses"] = len(
                [p for p in prospects if p.get("status") == "responded"]
            )
    else:
        prospects = []

    # Load and analyze customers database
    if os.path.exists("customers_database.json"):
        with open("customers_database.json") as f:
            customers = json.load(f)
            performance_log["customers"] = len(customers)
            performance_log["daily_revenue"] = (
                sum(c.get("mrr", 0) for c in customers) / 30
            )  # Convert MRR to daily
    else:
        customers = []

    # Save performance log
    logs.append(performance_log)
    with open("performance_log.json", "w") as f:
        json.dump(logs, f, indent=2)


if __name__ == "__main__":
    main()
