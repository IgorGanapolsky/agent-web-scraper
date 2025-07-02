#!/usr/bin/env python3
"""
LinkedIn Publisher
Publishes daily insights to LinkedIn via API
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class LinkedInPublisher:
    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.person_id = os.getenv("LINKEDIN_PERSON_ID")
        self.api_base = "https://api.linkedin.com/v2"

        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.linkedin_log_file = self.logs_dir / "linkedin_posts.csv"

        if not self.access_token:
            print("⚠️  LINKEDIN_ACCESS_TOKEN not configured, using dry run mode")
            self.dry_run = True
        else:
            self.dry_run = False

    def find_latest_report(self) -> Optional[Path]:
        """Find the latest daily report file"""
        reports_dir = Path("reports")
        today = datetime.now().strftime("%Y-%m-%d")

        # Try today's report first
        todays_report = reports_dir / f"insight_daily_{today}.md"
        if todays_report.exists():
            print(f"📄 Found today's report: {todays_report}")
            return todays_report

        # Find the most recent daily report
        daily_reports = list(reports_dir.glob("insight_daily_*.md"))
        if daily_reports:
            daily_reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_report = daily_reports[0]
            print(f"📄 Found latest daily report: {latest_report}")
            return latest_report

        print("❌ No daily reports found")
        return None

    def extract_linkedin_content(self, report_path: Path) -> dict:
        """Extract and format content for LinkedIn from the report"""
        try:
            with open(report_path, encoding="utf-8") as f:
                content = f.read()

            # Extract key insights
            lines = content.split("\n")
            insights = []
            niche_opportunities = []

            for i, line in enumerate(lines):
                # Extract key themes
                if "## 🎯 Key Themes Analysis" in line:
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith("##"):
                        if lines[j].startswith("### "):
                            insight = (
                                lines[j]
                                .replace("### ", "")
                                .replace("1. ", "")
                                .replace("2. ", "")
                                .replace("3. ", "")
                                .replace("4. ", "")
                            )
                            insights.append(insight)
                        j += 1

                # Extract niche opportunities
                if "🔍 Niche Saturation Check" in line:
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith("##"):
                        if "🔥 High" in lines[j] or "⚠️ Moderate" in lines[j]:
                            # Extract the keyword from previous line
                            if j > 0 and "🎯" in lines[j - 1]:
                                keyword = (
                                    lines[j - 1].replace("### 🎯 ", "").replace('"', "")
                                )
                                opportunity = (
                                    lines[j]
                                    .split("**Niche Opportunity Score:**")[1]
                                    .strip()
                                    if "**Niche Opportunity Score:**" in lines[j]
                                    else ""
                                )
                                niche_opportunities.append(f"{keyword}: {opportunity}")
                        j += 1

            # Create LinkedIn post
            today = datetime.now().strftime("%B %d, %Y")

            post_content = f"""🚀 Daily SaaS Market Intelligence - {today}

💡 TOP INSIGHTS FROM TODAY'S ANALYSIS:

"""

            # Add top insights
            for i, insight in enumerate(insights[:3], 1):
                post_content += f"{i}. {insight}\n"

            post_content += """
🎯 MARKET OPPORTUNITIES DISCOVERED:

"""

            # Add niche opportunities
            for opp in niche_opportunities[:2]:
                post_content += f"• {opp}\n"

            post_content += """
💬 What trends are you seeing in your SaaS market? Drop your insights below!

🔗 Get the full daily analysis: https://saasgrowthdispatch.com/insights

#SaaS #MarketResearch #AI #BusinessIntelligence #Entrepreneurship #TechTrends
"""

            return {
                "content": post_content,
                "title": f"Daily SaaS Market Intelligence - {today}",
                "hashtags": [
                    "SaaS",
                    "MarketResearch",
                    "AI",
                    "BusinessIntelligence",
                    "Entrepreneurship",
                ],
            }

        except Exception as e:
            print(f"❌ Error extracting content: {e}")
            return self.generate_fallback_content()

    def generate_fallback_content(self) -> dict:
        """Generate fallback content when extraction fails"""
        today = datetime.now().strftime("%B %d, %Y")

        content = f"""🚀 Daily SaaS Market Intelligence - {today}

📊 Today's AI-powered analysis reveals key opportunities in the SaaS landscape:

💡 Integration challenges continue to drive innovation opportunities
🎯 SMB AI adoption barriers present untapped markets
📈 Cost optimization needs create new tool categories

🔍 Our analysis found several HIGH opportunity niches with minimal competition.

💬 What's the biggest challenge in your SaaS market right now?

🔗 Full insights: https://saasgrowthdispatch.com/insights

#SaaS #MarketResearch #AI #BusinessIntelligence #Entrepreneurship
"""

        return {
            "content": content,
            "title": f"Daily SaaS Market Intelligence - {today}",
            "hashtags": [
                "SaaS",
                "MarketResearch",
                "AI",
                "BusinessIntelligence",
                "Entrepreneurship",
            ],
        }

    def publish_to_linkedin(self, post_data: dict) -> bool:
        """Publish content to LinkedIn"""
        if self.dry_run:
            print("🧪 DRY RUN MODE - Post would be published:")
            print(f"Title: {post_data['title']}")
            print(f"Content preview: {post_data['content'][:100]}...")
            print(f"Hashtags: {', '.join(post_data['hashtags'])}")
            return True

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }

            # LinkedIn UGC Post API payload
            payload = {
                "author": f"urn:li:person:{self.person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": post_data["content"]},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            }

            response = requests.post(
                f"{self.api_base}/ugcPosts", headers=headers, json=payload, 
            timeout=60)

            if response.status_code == 201:
                post_response = response.json()
                post_id = post_response.get("id", "")
                print(f"✅ Post published successfully to LinkedIn: {post_id}")
                return True
            else:
                print(f"❌ Error publishing to LinkedIn: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error publishing to LinkedIn: {e}")
            return False

    def log_linkedin_result(
        self, post_data: dict, success: bool, report_path: Path, error_msg: str = ""
    ):
        """Log LinkedIn publishing result to CSV"""

        # Create CSV header if file doesn't exist
        if not self.linkedin_log_file.exists():
            with open(self.linkedin_log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "report_file",
                        "title",
                        "content_length",
                        "hashtags",
                        "status",
                        "error_message",
                        "dry_run",
                    ]
                )

        # Log the result
        with open(self.linkedin_log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    datetime.now().isoformat(),
                    report_path.name,
                    post_data["title"],
                    len(post_data["content"]),
                    "|".join(post_data["hashtags"]),
                    "SUCCESS" if success else "FAILED",
                    error_msg,
                    self.dry_run,
                ]
            )

        print(f"📝 LinkedIn result logged to {self.linkedin_log_file}")

    def run(self) -> bool:
        """Execute the complete LinkedIn publishing pipeline"""
        print("🚀 Starting LinkedIn publishing...")

        # Step 1: Find the latest report
        print("\n📊 Finding latest report...")
        report_path = self.find_latest_report()
        if not report_path:
            return False

        # Step 2: Extract and format content
        print("\n📝 Creating LinkedIn post...")
        post_data = self.extract_linkedin_content(report_path)

        # Step 3: Publish to LinkedIn
        print("\n📤 Publishing to LinkedIn...")
        success = self.publish_to_linkedin(post_data)

        # Step 4: Log result
        print("\n📝 Logging result...")
        self.log_linkedin_result(
            post_data, success, report_path, "" if success else "Publishing failed"
        )

        if success:
            print("\n✅ LinkedIn publishing complete!")
            return True
        else:
            print("\n❌ LinkedIn publishing failed")
            return False


def main():
    publisher = LinkedInPublisher()
    success = publisher.run()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
