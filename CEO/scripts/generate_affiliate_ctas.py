#!/usr/bin/env python3
"""
Affiliate CTA Generator
Generates compelling affiliate CTAs based on daily insights
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class AffiliateCTAGenerator:
    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.cta_log_file = self.logs_dir / "affiliate_ctas.csv"

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

    def extract_pain_points_and_niches(self, report_path: Path) -> dict:
        """Extract pain points and niche opportunities from report"""
        try:
            with open(report_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            pain_points = []
            niches = []
            high_opportunity_niches = []

            # Extract pain points
            for i, line in enumerate(lines):
                if "**Recent Pain Points Identified:**" in line:
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith("**"):
                        if lines[j].startswith("- **"):
                            pain_point = (
                                lines[j].split(":**")[1]
                                if ":**" in lines[j]
                                else lines[j]
                            )
                            pain_points.append(pain_point.strip())
                        j += 1

                # Extract niche opportunities
                if "## 💡 Underserved SaaS Niches" in line:
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith("##"):
                        if lines[j].startswith("### "):
                            niche_name = (
                                lines[j]
                                .replace("### ", "")
                                .replace("1. ", "")
                                .replace("2. ", "")
                                .replace("3. ", "")
                            )
                            niches.append(niche_name)
                        j += 1

                # Extract high opportunity niches from SerpAPI analysis
                if "🔥 High" in line and "🎯" in lines[i - 1] if i > 0 else False:
                    keyword = lines[i - 1].replace("### 🎯 ", "").replace('"', "")
                    high_opportunity_niches.append(keyword)

            return {
                "pain_points": pain_points[:5],  # Top 5
                "niches": niches[:3],  # Top 3
                "high_opportunity_niches": high_opportunity_niches[:3],  # Top 3
            }

        except Exception as e:
            print(f"❌ Error extracting data: {e}")
            return {
                "pain_points": [
                    "Integration complexity",
                    "Cost optimization",
                    "Security gaps",
                ],
                "niches": [
                    "AI Integration Platform",
                    "Cost Optimization Tool",
                    "Security Compliance",
                ],
                "high_opportunity_niches": [
                    "ai onboarding automation",
                    "b2b lead scoring",
                ],
            }

    def generate_ctas_for_platform(self, platform: str, data: dict) -> list[dict]:
        """Generate platform-specific CTAs"""
        today = datetime.now().strftime("%Y-%m-%d")
        ctas = []

        # Base UTM parameters
        utm_base = f"?utm_source={platform}&utm_medium=social&utm_campaign=daily_insights_{today}"

        if platform == "linkedin":
            ctas = [
                {
                    "type": "pain_point_solution",
                    "headline": "Tired of SaaS Integration Headaches?",
                    "description": f"Based on today's analysis, {data['pain_points'][0]} is costing businesses 20+ hours per week.",
                    "cta_text": "Get the Integration Solution",
                    "url": f"https://saasgrowthdispatch.com/integration-guide{utm_base}&content=pain_point",
                    "pain_point": (
                        data["pain_points"][0]
                        if data["pain_points"]
                        else "integration issues"
                    ),
                },
                {
                    "type": "niche_opportunity",
                    "headline": f"🔥 HIGH Opportunity Market: {data['high_opportunity_niches'][0] if data['high_opportunity_niches'] else 'AI Automation'}",
                    "description": "Our SerpAPI analysis shows minimal competition but high demand. Perfect for validators.",
                    "cta_text": "Access Full Market Analysis",
                    "url": f"https://saasgrowthdispatch.com/niche-analysis{utm_base}&content=opportunity",
                    "niche": (
                        data["high_opportunity_niches"][0]
                        if data["high_opportunity_niches"]
                        else "AI automation"
                    ),
                },
                {
                    "type": "newsletter_signup",
                    "headline": "Get Daily SaaS Market Intelligence",
                    "description": "Join 2,500+ founders getting actionable insights delivered daily.",
                    "cta_text": "Subscribe Free",
                    "url": f"https://saasgrowthdispatch.com/subscribe{utm_base}&content=newsletter",
                    "benefit": "Daily market opportunities",
                },
            ]

        elif platform == "twitter":
            ctas = [
                {
                    "type": "thread_cta",
                    "headline": "Want the full analysis?",
                    "description": "🔗 Daily SaaS market intelligence with niche scoring",
                    "cta_text": "Get Free Insights",
                    "url": f"https://saasgrowthdispatch.com/insights{utm_base}&content=thread",
                    "hook": "What markets are you exploring? 👇",
                },
                {
                    "type": "tool_promotion",
                    "headline": f"Validate '{data['high_opportunity_niches'][0] if data['high_opportunity_niches'] else 'your idea'}' in 5 minutes",
                    "description": "Use our niche scoring tool to find blue ocean markets",
                    "cta_text": "Try Free Tool",
                    "url": f"https://saasgrowthdispatch.com/niche-scorer{utm_base}&content=tool",
                    "benefit": "Instant opportunity scoring",
                },
            ]

        elif platform == "substack":
            ctas = [
                {
                    "type": "premium_upgrade",
                    "headline": "Upgrade to Premium Analysis",
                    "description": "Get weekly deep-dives into the most profitable SaaS opportunities with detailed implementation guides.",
                    "cta_text": "Upgrade to Premium",
                    "url": f"https://saasgrowthdispatch.com/premium{utm_base}&content=upgrade",
                    "benefit": "Weekly deep-dive reports + implementation guides",
                },
                {
                    "type": "case_study",
                    "headline": "See How Others Found Their $50K+ Niches",
                    "description": "Real case studies of founders who used our analysis to build profitable SaaS products.",
                    "cta_text": "View Case Studies",
                    "url": f"https://saasgrowthdispatch.com/case-studies{utm_base}&content=social_proof",
                    "social_proof": "Join 47 successful founders",
                },
            ]

        elif platform == "tiktok":
            ctas = [
                {
                    "type": "quick_win",
                    "headline": "Find Your SaaS Niche in 60 Seconds",
                    "description": "Free tool that analyzes market saturation instantly",
                    "cta_text": "Try Now (Free)",
                    "url": f"https://saasgrowthdispatch.com/quick-niche{utm_base}&content=tiktok_tool",
                    "urgency": "Results in 60 seconds",
                }
            ]

        return ctas

    def generate_all_platform_ctas(self, data: dict) -> dict:
        """Generate CTAs for all platforms"""
        platforms = ["linkedin", "twitter", "substack", "tiktok"]
        all_ctas = {}

        for platform in platforms:
            all_ctas[platform] = self.generate_ctas_for_platform(platform, data)

        return all_ctas

    def save_ctas_to_json(self, ctas: dict, report_path: Path) -> Path:
        """Save generated CTAs to JSON file"""
        today = datetime.now().strftime("%Y-%m-%d")
        cta_file = Path("logs") / f"affiliate_ctas_{today}.json"

        with open(cta_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": datetime.now().isoformat(),
                    "source_report": report_path.name,
                    "ctas": ctas,
                },
                f,
                indent=2,
            )

        print(f"💾 CTAs saved to {cta_file}")
        return cta_file

    def log_cta_generation(self, ctas: dict, report_path: Path, success: bool):
        """Log CTA generation results"""

        # Create CSV header if file doesn't exist
        if not self.cta_log_file.exists():
            with open(self.cta_log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "report_file",
                        "platforms",
                        "total_ctas",
                        "linkedin_ctas",
                        "twitter_ctas",
                        "substack_ctas",
                        "tiktok_ctas",
                        "status",
                    ]
                )

        # Log the result
        with open(self.cta_log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            platform_counts = {
                platform: len(cta_list) for platform, cta_list in ctas.items()
            }
            total_ctas = sum(platform_counts.values())

            writer.writerow(
                [
                    datetime.now().isoformat(),
                    report_path.name,
                    "|".join(ctas.keys()),
                    total_ctas,
                    platform_counts.get("linkedin", 0),
                    platform_counts.get("twitter", 0),
                    platform_counts.get("substack", 0),
                    platform_counts.get("tiktok", 0),
                    "SUCCESS" if success else "FAILED",
                ]
            )

        print(f"📝 CTA generation logged to {self.cta_log_file}")

    def run(self) -> bool:
        """Execute the complete CTA generation pipeline"""
        print("🚀 Starting affiliate CTA generation...")

        # Step 1: Find the latest report
        print("\n📊 Finding latest report...")
        report_path = self.find_latest_report()
        if not report_path:
            return False

        # Step 2: Extract pain points and niches
        print("\n🔍 Extracting pain points and opportunities...")
        data = self.extract_pain_points_and_niches(report_path)
        print(
            f"✅ Extracted {len(data['pain_points'])} pain points, {len(data['niches'])} niches"
        )

        # Step 3: Generate CTAs for all platforms
        print("\n📝 Generating platform-specific CTAs...")
        all_ctas = self.generate_all_platform_ctas(data)

        total_ctas = sum(len(ctas) for ctas in all_ctas.values())
        print(f"✅ Generated {total_ctas} CTAs across {len(all_ctas)} platforms")

        # Step 4: Save CTAs to JSON
        print("\n💾 Saving CTAs...")
        cta_file = self.save_ctas_to_json(all_ctas, report_path)

        # Step 5: Log results
        print("\n📝 Logging results...")
        self.log_cta_generation(all_ctas, report_path, True)

        print("\n✅ Affiliate CTA generation complete!")
        print(f"📄 CTAs saved to: {cta_file}")

        return True


def main():
    generator = AffiliateCTAGenerator()
    success = generator.run()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
