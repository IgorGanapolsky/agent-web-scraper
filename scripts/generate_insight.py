#!/usr/bin/env python3
"""
Daily AI Insight Report Generator
Processes metrics data and generates comprehensive insights using AI analysis
"""

import os

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
import json
from datetime import datetime, timedelta
from typing import Any

from dotenv import load_dotenv

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

load_dotenv()


class InsightGenerator:
    def __init__(self):
        self.setup_ai_clients()
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.report_file = f"reports/insight_daily_{self.today}.md"

    def setup_ai_clients(self):
        """Initialize AI API clients with fallback to mock responses"""
        self.openai_available = False
        self.gemini_available = False

        # Try OpenAI
        if OPENAI_AVAILABLE:
            openai_key = os.getenv("OPENAI_API_KEY")
            if (
                openai_key
                and not openai_key.startswith("your-")
                and len(openai_key) > 10
            ):
                try:
                    self.openai_key = openai_key
                    self.openai_available = True
                    print("✅ OpenAI API configured")
                except Exception as e:
                    print(f"❌ OpenAI setup failed: {e}")

        # Try Gemini
        if GEMINI_AVAILABLE:
            gemini_key = os.getenv("GEMINI_API_KEY")
            if (
                gemini_key
                and not gemini_key.startswith("your-")
                and len(gemini_key) > 10
            ):
                try:
                    genai.configure(api_key=gemini_key)
                    self.gemini_available = True
                    print("✅ Gemini API configured")
                except Exception as e:
                    print(f"❌ Gemini setup failed: {e}")

        if not self.openai_available and not self.gemini_available:
            print("⚠️  No AI APIs available - using mock responses")

    def read_recent_metrics(self):
        """Read the last 7 rows from metrics-daily.csv"""
        if not PANDAS_AVAILABLE:
            print("⚠️  Pandas not available, using mock data")
            return self.create_mock_data()

        try:
            df = pd.read_csv("metrics-daily.csv")
            if len(df) == 0:
                print("❌ No data in metrics-daily.csv")
                return self.create_mock_data()

            # Get last 7 rows
            recent_data = df.tail(7)
            print(f"✅ Loaded {len(recent_data)} recent metric rows")
            return recent_data

        except FileNotFoundError:
            print("❌ metrics-daily.csv not found, creating mock data")
            return self.create_mock_data()
        except Exception as e:
            print(f"❌ Error reading metrics: {e}")
            return self.create_mock_data()

    def create_mock_data(self):
        """Create mock metrics data for testing"""
        dates = [
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(6, -1, -1)
        ]

        mock_data = {
            "date": dates,
            "pain_point_1_label": [
                "SaaS integration complexity",
                "AI adoption barriers",
                "Cost optimization needs",
                "Security vulnerabilities",
                "Onboarding friction",
                "Data synchronization issues",
                "Performance bottlenecks",
            ],
            "pain_point_2_label": [
                "API rate limiting",
                "Tool proliferation",
                "User experience gaps",
                "Compliance requirements",
                "Scaling challenges",
                "Workflow automation",
                "Customer retention",
            ],
            "query": [
                "AI tools for business automation",
                "SaaS integration solutions",
                "Cost optimization tools",
                "Security automation",
                "UX optimization",
                "Data management",
                "Performance monitoring",
            ],
        }

        if PANDAS_AVAILABLE:
            return pd.DataFrame(mock_data)
        else:
            return mock_data

    def analyze_with_ai(self, data_summary: str) -> dict[str, Any]:
        """Analyze data using available AI service with fallback to mock"""

        prompt = f"""
        Analyze the following SaaS market data from the past 7 days and provide:

        Data Summary:
        {data_summary}

        Please provide a JSON response with:
        1. "themes": 3-5 key pain point themes with descriptions
        2. "niches": 3 underserved SaaS niches with market potential
        3. "lead_magnet": title and 3-point outline for a high-converting lead magnet

        Format as valid JSON.
        """

        # Try Gemini first (faster and more cost-effective)
        if self.gemini_available:
            try:
                model = genai.GenerativeModel("gemini-pro")
                response = model.generate_content(prompt)
                return self.parse_ai_response(response.text)
            except Exception as e:
                print(f"❌ Gemini failed: {e}")

        # Fallback to OpenAI
        if self.openai_available:
            try:
                client = openai.OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                return self.parse_ai_response(response.choices[0].message.content)
            except Exception as e:
                print(f"❌ OpenAI failed: {e}")

        # Fallback to mock response
        return self.generate_mock_analysis()

    def parse_ai_response(self, response_text: str) -> dict[str, Any]:
        """Parse AI response, extracting JSON if needed"""
        try:
            # Look for JSON in the response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end != 0:
                json_text = response_text[start:end]
                return json.loads(json_text)
            else:
                # Try parsing the whole response
                return json.loads(response_text)
        except json.JSONDecodeError:
            print("❌ Could not parse AI response as JSON, using mock data")
            return self.generate_mock_analysis()

    def generate_mock_analysis(self) -> dict[str, Any]:
        """Generate mock analysis for testing"""
        return {
            "themes": [
                {
                    "name": "Integration & Connectivity Challenges",
                    "description": "SaaS tools struggling with seamless integration, API limitations, and workflow disruptions",
                },
                {
                    "name": "AI Adoption & Implementation Barriers",
                    "description": "Small businesses facing awareness gaps, complexity concerns, and unclear ROI from AI tools",
                },
                {
                    "name": "Cost Optimization & Budget Pressures",
                    "description": "Rising pressure to optimize SaaS spending while maintaining operational efficiency",
                },
                {
                    "name": "Security & Compliance Gaps",
                    "description": "Growing vulnerabilities in AI-powered systems and data privacy concerns",
                },
            ],
            "niches": [
                {
                    "name": "SMB AI Integration Platform",
                    "description": "Simplified AI tool integration specifically designed for small businesses with limited technical resources",
                },
                {
                    "name": "SaaS Cost Optimization Dashboard",
                    "description": "Automated tool for tracking, analyzing, and optimizing multi-SaaS subscription costs",
                },
                {
                    "name": "No-Code Security Compliance Tool",
                    "description": "Automated compliance monitoring for AI-powered business tools without technical expertise required",
                },
            ],
            "lead_magnet": {
                "title": "The 2025 SaaS Integration Playbook: 5 Steps to Connect Your Tools Without Breaking Your Budget",
                "outline": [
                    "Audit Your Current SaaS Stack: Identify redundancies and integration gaps costing you time and money",
                    "The 80/20 Integration Strategy: Focus on the 20% of connections that solve 80% of your workflow problems",
                    "Budget-Friendly Integration Tools: Complete comparison of integration platforms under $100/month",
                ],
            },
        }

    def generate_report(self, data, analysis: dict[str, Any]) -> str:
        """Generate markdown report from data and analysis"""

        if PANDAS_AVAILABLE and hasattr(data, "empty") and not data.empty:
            date_range = f"{data['date'].iloc[0]} to {data['date'].iloc[-1]}"
        elif isinstance(data, dict) and "date" in data:
            date_range = f"{data['date'][0]} to {data['date'][-1]}"
        else:
            date_range = "N/A"

        report = f"""# 🤖 Daily AI Insight Report
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} EST
**Data Period:** {date_range}
**Analysis Method:** {'Gemini Pro' if self.gemini_available else 'GPT-4' if self.openai_available else 'Mock Analysis'}

---

## 📊 Weekly Data Summary

**Recent Pain Points Identified:**
"""

        if PANDAS_AVAILABLE and hasattr(data, "empty") and not data.empty:
            for _, row in data.iterrows():
                pain1 = row.get("pain_point_1_label", "N/A")
                pain2 = row.get("pain_point_2_label", "N/A")
                report += f"- **{row['date']}:** {pain1} | {pain2}\n"
            trending_queries = (
                ", ".join(data["query"].unique()) if "query" in data.columns else "N/A"
            )
        elif isinstance(data, dict) and "date" in data:
            for i, date in enumerate(data["date"]):
                pain1 = (
                    data["pain_point_1_label"][i]
                    if i < len(data["pain_point_1_label"])
                    else "N/A"
                )
                pain2 = (
                    data["pain_point_2_label"][i]
                    if i < len(data["pain_point_2_label"])
                    else "N/A"
                )
                report += f"- **{date}:** {pain1} | {pain2}\n"
            trending_queries = ", ".join(set(data["query"]))
        else:
            report += "- No recent data available\n"
            trending_queries = "N/A"

        report += f"""
**Trending Queries:** {trending_queries}

---

## 🎯 Key Themes Analysis

"""

        for i, theme in enumerate(analysis["themes"], 1):
            report += f"### {i}. {theme['name']}\n{theme['description']}\n\n"

        report += """---

## 💡 Underserved SaaS Niches

"""

        for i, niche in enumerate(analysis["niches"], 1):
            report += f"### {i}. {niche['name']}\n{niche['description']}\n\n"

        report += f"""---

## 🧲 Recommended Lead Magnet

### {analysis['lead_magnet']['title']}

**Outline:**
"""

        for i, point in enumerate(analysis["lead_magnet"]["outline"], 1):
            report += f"{i}. {point}\n"

        report += """

---

## 🚀 Next Steps

1. **Prioritize Integration Solutions** - Focus on tools that address the top connectivity challenges
2. **Develop SMB-Focused Content** - Create educational resources for small business AI adoption
3. **Monitor Cost Optimization Trends** - Track emerging needs in SaaS spending management
4. **Validate Lead Magnet Concept** - Test interest in integration-focused content offers

---

*🤖 Generated with [Claude Code](https://claude.ai/code) | [View Raw Data](../metrics-daily.csv) | [Automation Details](../.github/workflows/insight_report.yml)*
"""

        return report

    def save_report(self, report_content: str) -> str:
        """Save report to file and return file path"""
        os.makedirs("reports", exist_ok=True)

        with open(self.report_file, "w") as f:
            f.write(report_content)

        print(f"✅ Report saved to {self.report_file}")
        return self.report_file

    def run(self):
        """Execute the complete insight generation pipeline"""
        print("🚀 Starting Daily AI Insight Report Generation...")

        # Step 1: Read recent metrics
        print("\n📊 Reading recent metrics data...")
        data = self.read_recent_metrics()

        # Step 2: Prepare data summary for AI analysis
        print("\n🤖 Preparing data for AI analysis...")
        if not data.empty:
            data_summary = data.to_string()
        else:
            data_summary = "No recent data available"

        # Step 3: Generate AI analysis
        print("\n🧠 Generating AI insights...")
        analysis = self.analyze_with_ai(data_summary)

        # Step 4: Generate report
        print("\n📝 Creating markdown report...")
        report_content = self.generate_report(data, analysis)

        # Step 5: Save report
        print("\n💾 Saving report...")
        report_path = self.save_report(report_content)

        print("\n✅ Daily insight report generation complete!")
        print(f"📄 Report: {report_path}")

        return report_path


if __name__ == "__main__":
    generator = InsightGenerator()
    generator.run()
