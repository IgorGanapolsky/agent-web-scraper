#!/usr/bin/env python3
"""
Alternative GitHub Issues creation using different approach
"""

import json
import os
import subprocess

from dotenv import load_dotenv

load_dotenv()


# Try alternative approaches
def create_issue_via_curl(title, body, labels):
    """Create issue using curl directly"""
    token = os.getenv("GITHUB_TOKEN")

    issue_data = {"title": title, "body": body, "labels": labels}

    curl_cmd = [
        "curl",
        "-X",
        "POST",
        "-H",
        f"Authorization: token {token}",
        "-H",
        "Accept: application/vnd.github.v3+json",
        "-H",
        "User-Agent: agent-web-scraper-automation",
        "https://api.github.com/repos/IgorGanapolsky/agent-web-scraper/issues",
        "-d",
        json.dumps(issue_data),
    ]

    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        print(f"Status: {result.returncode}")
        print(f"Response: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False


# Test with first issue
if __name__ == "__main__":
    success = create_issue_via_curl(
        "Add Stripe integration for monetization",
        "Implement Stripe payment workflow for paid research packs to enable revenue generation from the platform.",
        ["enhancement", "high-priority", "business"],
    )
    print(f"Issue creation success: {success}")
