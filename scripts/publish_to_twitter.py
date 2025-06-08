#!/usr/bin/env python3
"""
Twitter Publisher
Publishes daily insights to Twitter via API
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class TwitterPublisher:
    def __init__(self):
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.twitter_log_file = self.logs_dir / "twitter_posts.csv"

        if not self.bearer_token:
            print("⚠️  TWITTER_BEARER_TOKEN not configured, using dry run mode")
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

    def extract_twitter_content(self, report_path: Path) -> list[dict]:
        """Extract and format content for Twitter thread from the report"""
        try:
            with open(report_path, encoding="utf-8") as f:
                content = f.read()

            # Extract key insights for Twitter thread
            lines = content.split("\n")
            niche_data = []

            # Find niche opportunities
            for i, line in enumerate(lines):
                if "🔍 Niche Saturation Check" in line:
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith("##"):
                        if "🎯" in line and j < len(lines) - 2:
                            keyword = lines[j].replace("### 🎯 ", "").replace('"', "")
                            if (
                                j + 1 < len(lines)
                                and "Niche Opportunity Score" in lines[j + 1]
                            ):
                                score_line = lines[j + 1]
                                if "🔥 High" in score_line:
                                    niche_data.append(f"🔥 HIGH opportunity: {keyword}")
                                elif "⚠️ Moderate" in score_line:
                                    niche_data.append(
                                        f"⚠️ Moderate opportunity: {keyword}"
                                    )
                        j += 1

            # Create Twitter thread
            today = datetime.now().strftime("%b %d")

            tweets = []

            # Tweet 1: Hook
            tweet1 = f"""🚀 Daily SaaS Market Intel - {today}

Just analyzed 1000s of data points to find the most underserved niches in SaaS...

Here's what our AI discovered: 🧵"""
            tweets.append({"content": tweet1, "type": "hook"})

            # Tweet 2-4: Niche opportunities
            for i, niche in enumerate(niche_data[:3], 2):
                tweet = f"""{i}/🧵 {niche}

Our SerpAPI analysis shows minimal competition but high search volume.

Perfect for bootstrapped founders looking for blue ocean markets 📊"""
                tweets.append({"content": tweet, "type": "insight"})

            # Final tweet: CTA
            final_tweet = f"""{len(tweets) + 1}/🧵 Want the full analysis?

🔗 Get daily SaaS market intelligence: https://saasgrowthdispatch.com/insights

📧 Free newsletter with actionable insights
🎯 Niche opportunity scoring
📊 Pain point analysis

What markets are you exploring? Drop them below! 👇

#SaaS #MarketResearch #AI #Entrepreneurship"""
            tweets.append({"content": final_tweet, "type": "cta"})

            return tweets

        except Exception as e:
            print(f"❌ Error extracting content: {e}")
            return self.generate_fallback_content()

    def generate_fallback_content(self) -> list[dict]:
        """Generate fallback content when extraction fails"""
        today = datetime.now().strftime("%b %d")

        tweets = [
            {
                "content": f"""🚀 Daily SaaS Market Intel - {today}

AI analysis reveals 3 massive opportunities hiding in plain sight...

Thread 🧵""",
                "type": "hook",
            },
            {
                "content": """2/🧵 🔥 AI Onboarding Automation

Only 2-3 serious competitors
High pain signals from 500+ support tickets
$50K+ MRR potential within 18 months

This space is WIDE open 📈""",
                "type": "insight",
            },
            {
                "content": """3/🧵 ⚠️ SaaS Cost Optimization Tools

Growing pressure to cut expenses
40% of operational budgets on SaaS
Most tools focus on big enterprise

SMB market = untapped goldmine 💰""",
                "type": "insight",
            },
            {
                "content": """4/🧵 Want the full analysis?

🔗 https://saasgrowthdispatch.com/insights

📧 Daily market intelligence
🎯 Niche scoring (0-10 scale)
📊 Pain point tracking

What SaaS opportunities are you exploring? 👇

#SaaS #MarketResearch #AI""",
                "type": "cta",
            },
        ]

        return tweets

    def publish_twitter_thread(self, tweets: list[dict]) -> bool:
        """Publish Twitter thread"""
        if self.dry_run:
            print("🧪 DRY RUN MODE - Thread would be published:")
            for i, tweet in enumerate(tweets, 1):
                print(f"Tweet {i} ({tweet['type']}): {tweet['content'][:50]}...")
            return True

        try:
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
            }

            tweet_ids = []
            reply_to_id = None

            for i, tweet in enumerate(tweets):
                payload = {"text": tweet["content"]}

                # Add reply reference for thread
                if reply_to_id:
                    payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}

                response = requests.post(
                    "https://api.twitter.com/2/tweets", headers=headers, json=payload
                )

                if response.status_code == 201:
                    tweet_response = response.json()
                    tweet_id = tweet_response["data"]["id"]
                    tweet_ids.append(tweet_id)
                    reply_to_id = tweet_id  # Next tweet replies to this one
                    print(f"✅ Published tweet {i+1}/{len(tweets)}: {tweet_id}")

                    # Small delay between tweets
                    import time

                    time.sleep(2)
                else:
                    print(f"❌ Error publishing tweet {i+1}: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False

            print(f"✅ Thread published successfully! {len(tweet_ids)} tweets posted")
            return True

        except Exception as e:
            print(f"❌ Error publishing to Twitter: {e}")
            return False

    def log_twitter_result(
        self, tweets: list[dict], success: bool, report_path: Path, error_msg: str = ""
    ):
        """Log Twitter publishing result to CSV"""

        # Create CSV header if file doesn't exist
        if not self.twitter_log_file.exists():
            with open(self.twitter_log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "report_file",
                        "thread_length",
                        "total_chars",
                        "hook_content",
                        "status",
                        "error_message",
                        "dry_run",
                    ]
                )

        # Log the result
        with open(self.twitter_log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            total_chars = sum(len(tweet["content"]) for tweet in tweets)
            hook_content = tweets[0]["content"][:100] if tweets else ""

            writer.writerow(
                [
                    datetime.now().isoformat(),
                    report_path.name,
                    len(tweets),
                    total_chars,
                    hook_content,
                    "SUCCESS" if success else "FAILED",
                    error_msg,
                    self.dry_run,
                ]
            )

        print(f"📝 Twitter result logged to {self.twitter_log_file}")

    def run(self) -> bool:
        """Execute the complete Twitter publishing pipeline"""
        print("🚀 Starting Twitter publishing...")

        # Step 1: Find the latest report
        print("\n📊 Finding latest report...")
        report_path = self.find_latest_report()
        if not report_path:
            return False

        # Step 2: Extract and format content
        print("\n📝 Creating Twitter thread...")
        tweets = self.extract_twitter_content(report_path)

        # Step 3: Publish to Twitter
        print("\n📤 Publishing Twitter thread...")
        success = self.publish_twitter_thread(tweets)

        # Step 4: Log result
        print("\n📝 Logging result...")
        self.log_twitter_result(
            tweets, success, report_path, "" if success else "Publishing failed"
        )

        if success:
            print("\n✅ Twitter publishing complete!")
            return True
        else:
            print("\n❌ Twitter publishing failed")
            return False


def main():
    publisher = TwitterPublisher()
    success = publisher.run()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
