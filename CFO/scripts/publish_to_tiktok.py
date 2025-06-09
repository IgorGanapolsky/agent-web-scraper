#!/usr/bin/env python3
"""
TikTok Content Generator
Generates TikTok-ready content ideas and scripts from daily insights
(Manual posting required due to TikTok API limitations)
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class TikTokContentGenerator:
    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.tiktok_log_file = self.logs_dir / "tiktok_content.csv"

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

    def extract_tiktok_hooks(self, report_path: Path) -> list[dict]:
        """Extract engaging hooks and content ideas for TikTok"""
        try:
            with open(report_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            high_opportunity_niches = []
            pain_points = []

            # Extract high opportunity niches
            for i, line in enumerate(lines):
                if "🔥 High" in line and i > 0 and "🎯" in lines[i - 1]:
                    keyword = lines[i - 1].replace("### 🎯 ", "").replace('"', "")
                    score_line = line
                    high_opportunity_niches.append(
                        {
                            "keyword": keyword,
                            "opportunity": "HIGH",
                            "score_line": score_line,
                        }
                    )
                elif "⚠️ Moderate" in line and i > 0 and "🎯" in lines[i - 1]:
                    keyword = lines[i - 1].replace("### 🎯 ", "").replace('"', "")
                    high_opportunity_niches.append(
                        {
                            "keyword": keyword,
                            "opportunity": "MODERATE",
                            "score_line": line,
                        }
                    )

            # Extract pain points
            for i, line in enumerate(lines):
                if "**Recent Pain Points Identified:**" in line:
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith("**"):
                        if lines[j].startswith("- **") and ":" in lines[j]:
                            pain_point = (
                                lines[j].split(":**")[1].strip()
                                if ":**" in lines[j]
                                else lines[j].strip()
                            )
                            pain_points.append(pain_point)
                        j += 1

            return self.generate_tiktok_concepts(high_opportunity_niches, pain_points)

        except Exception as e:
            print(f"❌ Error extracting content: {e}")
            return self.generate_fallback_concepts()

    def generate_tiktok_concepts(
        self, niches: list[dict], pain_points: list[str]
    ) -> list[dict]:
        """Generate TikTok video concepts based on extracted data"""
        concepts = []

        # Concept 1: Market Opportunity Hook
        if niches:
            top_niche = niches[0]
            concepts.append(
                {
                    "type": "market_opportunity",
                    "hook": f"I found a ${50000}+/month SaaS opportunity that nobody's talking about...",
                    "script": f"""Hook: "I found a $50K+/month SaaS opportunity that nobody's talking about..."

🎯 OPPORTUNITY: {top_niche['keyword']}

The Problem:
• {pain_points[0] if pain_points else 'Businesses struggle with manual processes'}
• Costs companies 20+ hours per week
• No good solutions exist

The Market:
• HIGH opportunity ({top_niche['opportunity']})
• Minimal competition found
• High search volume

The Solution Opportunity:
• Simple automation tool
• $49-199/month pricing
• Target: small businesses

Want to validate this idea?
→ Check comments for free validation tool

#SaaS #Entrepreneurship #BusinessIdeas #AI #MarketResearch""",
                    "visual_cues": [
                        "Show market analysis dashboard",
                        "Highlight opportunity score",
                        "Demo competitor research",
                        "Show potential revenue calculator",
                    ],
                    "cta": "Get the free market validation tool in comments!",
                    "hashtags": [
                        "#SaaS",
                        "#Entrepreneurship",
                        "#BusinessIdeas",
                        "#AI",
                        "#MarketResearch",
                    ],
                }
            )

        # Concept 2: Problem/Solution Story
        if pain_points:
            concepts.append(
                {
                    "type": "problem_solution",
                    "hook": f"Why are 1000s of businesses still struggling with {pain_points[0][:30]}...",
                    "script": f"""Hook: "Why are 1000s of businesses still struggling with {pain_points[0]}..."

The Reality:
• Analyzed 500+ support tickets
• Same problem keeps appearing
• Costing businesses $1000s monthly

Current "Solutions":
• Expensive enterprise tools
• Complex setups requiring devs
• Band-aid fixes that break

The Opportunity:
• Build something simple
• Focus on small businesses
• $49/month price point

Market Size:
• {len(pain_points)} major pain points identified
• Millions of potential customers
• Growing 25% yearly

Ready to dive deeper?
→ Daily market insights in bio

#PainPoints #SaaS #MarketGap #BusinessOpportunity""",
                    "visual_cues": [
                        "Show support ticket examples",
                        "Highlight current solution problems",
                        "Display market size stats",
                        "Show simple solution mockup",
                    ],
                    "cta": "Follow for daily SaaS opportunities!",
                    "hashtags": [
                        "#PainPoints",
                        "#SaaS",
                        "#MarketGap",
                        "#BusinessOpportunity",
                    ],
                }
            )

        # Concept 3: Quick Market Analysis
        concepts.append(
            {
                "type": "market_analysis",
                "hook": "I analyzed 1000+ SaaS tools in 60 seconds. Here's what I found...",
                "script": f"""Hook: "I analyzed 1000+ SaaS tools in 60 seconds. Here's what I found..."

The Process:
• AI-powered market analysis
• SerpAPI competitor research
• Reddit pain point mining
• Opportunity scoring (0-10)

Today's Results:
• {len(niches)} HIGH opportunity niches
• {len(pain_points)} major pain points
• Minimal competition found

Best Opportunity:
• {niches[0]['keyword'] if niches else 'AI automation tools'}
• Score: {9 if niches and niches[0]['opportunity'] == 'HIGH' else 7}/10
• Revenue potential: $50K+ monthly

The Tool:
• Free market scanner
• Instant opportunity scoring
• Daily insights delivered

Link in bio for free access!

#MarketResearch #SaaS #AI #BusinessAnalysis #Entrepreneurship""",
                "visual_cues": [
                    "Screen record analysis tool",
                    "Show live data processing",
                    "Highlight opportunity scores",
                    "Display final results dashboard",
                ],
                "cta": "Get free access - link in bio!",
                "hashtags": [
                    "#MarketResearch",
                    "#SaaS",
                    "#AI",
                    "#BusinessAnalysis",
                    "#Entrepreneurship",
                ],
            }
        )

        # Concept 4: Behind the Scenes
        concepts.append(
            {
                "type": "behind_scenes",
                "hook": "Building a $100K SaaS from market data (Day 1)...",
                "script": f"""Hook: "Building a $100K SaaS from market data (Day 1)..."

The Plan:
• Find underserved market
• Validate with real users
• Build MVP in 30 days
• Document everything

Today's Discovery:
• Market: {niches[0]['keyword'] if niches else 'automation tools'}
• Problem: {pain_points[0][:50] if pain_points else 'manual processes'}
• Competition: MINIMAL
• Opportunity: HIGH

Next Steps:
• Interview 10 potential users
• Create landing page
• Build waitlist
• Start coding

Following this journey?
→ Daily updates in stories
→ Full analysis in bio

Who's building with me?

#BuildInPublic #SaaS #Entrepreneurship #StartupJourney""",
                "visual_cues": [
                    "Show workspace setup",
                    "Display market research",
                    "Sketch out user journey",
                    "Show competitor analysis",
                ],
                "cta": "Follow the journey - updates daily!",
                "hashtags": [
                    "#BuildInPublic",
                    "#SaaS",
                    "#Entrepreneurship",
                    "#StartupJourney",
                ],
            }
        )

        return concepts

    def generate_fallback_concepts(self) -> list[dict]:
        """Generate fallback concepts when data extraction fails"""
        return [
            {
                "type": "market_opportunity",
                "hook": "I found a $50K+/month SaaS opportunity that nobody's talking about...",
                "script": """Hook: "I found a $50K+/month SaaS opportunity..."

The market gap in AI automation is MASSIVE.

Most tools are too complex for small businesses.
But the demand is exploding.

Simple solution = big opportunity.

#SaaS #AI #BusinessOpportunity""",
                "visual_cues": ["Market analysis", "Opportunity dashboard"],
                "cta": "Want the full analysis?",
                "hashtags": ["#SaaS", "#AI", "#BusinessOpportunity"],
            }
        ]

    def save_concepts_to_json(self, concepts: list[dict], report_path: Path) -> Path:
        """Save TikTok concepts to JSON file"""
        today = datetime.now().strftime("%Y-%m-%d")
        concept_file = self.logs_dir / f"tiktok_concepts_{today}.json"

        with open(concept_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": datetime.now().isoformat(),
                    "source_report": report_path.name,
                    "concepts": concepts,
                    "posting_instructions": {
                        "timing": "Post between 6-9 PM EST for best engagement",
                        "format": "Vertical video (9:16 ratio)",
                        "duration": "15-30 seconds optimal",
                        "trending_sounds": "Use trending audio when possible",
                        "visual_style": "Fast-paced with text overlays",
                    },
                },
                f,
                indent=2,
            )

        print(f"💾 TikTok concepts saved to {concept_file}")
        return concept_file

    def log_generation_result(
        self, concepts: list[dict], report_path: Path, success: bool
    ):
        """Log TikTok content generation results"""

        # Create CSV header if file doesn't exist
        if not self.tiktok_log_file.exists():
            with open(self.tiktok_log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "report_file",
                        "concepts_generated",
                        "concept_types",
                        "primary_hook",
                        "status",
                    ]
                )

        # Log the result
        with open(self.tiktok_log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            concept_types = "|".join({concept["type"] for concept in concepts})
            primary_hook = concepts[0]["hook"] if concepts else ""

            writer.writerow(
                [
                    datetime.now().isoformat(),
                    report_path.name,
                    len(concepts),
                    concept_types,
                    primary_hook[:100],
                    "SUCCESS" if success else "FAILED",
                ]
            )

        print(f"📝 TikTok generation logged to {self.tiktok_log_file}")

    def run(self) -> bool:
        """Execute the complete TikTok content generation pipeline"""
        print("🚀 Starting TikTok content generation...")

        # Step 1: Find the latest report
        print("\n📊 Finding latest report...")
        report_path = self.find_latest_report()
        if not report_path:
            return False

        # Step 2: Generate TikTok concepts
        print("\n🎬 Generating TikTok video concepts...")
        concepts = self.extract_tiktok_hooks(report_path)
        print(f"✅ Generated {len(concepts)} video concepts")

        # Step 3: Save concepts to JSON
        print("\n💾 Saving concepts...")
        concept_file = self.save_concepts_to_json(concepts, report_path)

        # Step 4: Log results
        print("\n📝 Logging results...")
        self.log_generation_result(concepts, report_path, True)

        print("\n✅ TikTok content generation complete!")
        print(f"📄 Concepts saved to: {concept_file}")
        print("\n🎬 MANUAL POSTING REQUIRED:")
        print("1. Review generated concepts in the JSON file")
        print("2. Create videos based on scripts and visual cues")
        print("3. Post during optimal times (6-9 PM EST)")
        print("4. Use trending audio when possible")

        return True


def main():
    generator = TikTokContentGenerator()
    success = generator.run()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
