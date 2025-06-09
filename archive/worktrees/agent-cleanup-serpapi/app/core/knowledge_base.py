#!/usr/bin/env python3
"""
Knowledge Base Ingestion System for Agentic RAG
Converts existing data sources into structured documents for vector indexing
"""

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
from llama_index.core import Document

from app.utils.analytics import performance_monitor


class KnowledgeBaseBuilder:
    """Builds knowledge base from existing data sources"""

    def __init__(self):
        """Initialize the knowledge base builder"""

        self.data_dir = Path("data")
        self.reports_dir = Path("reports")
        self.logs_dir = Path("logs")

        print("📚 Knowledge Base Builder initialized")

    @performance_monitor
    async def build_reddit_knowledge_base(self) -> list[Document]:
        """Build Reddit pain points knowledge base from existing data"""

        print("🔧 Building Reddit pain points knowledge base...")

        documents = []

        # Load from metrics CSV files
        metrics_files = list(self.data_dir.glob("metrics-*.csv"))

        for metrics_file in metrics_files:
            try:
                df = pd.read_csv(metrics_file)

                # Process each pain point entry
                for _, row in df.iterrows():
                    if pd.notna(row.get("pain_point", "")):
                        doc_text = self._format_reddit_document(row)

                        metadata = {
                            "source": "reddit",
                            "data_type": "pain_point",
                            "date": row.get("date", ""),
                            "subreddit": row.get("subreddit", ""),
                            "score": row.get("score", 0),
                            "comment_count": row.get("comment_count", 0),
                            "category": self._categorize_pain_point(
                                row.get("pain_point", "")
                            ),
                            "urgency": self._assess_urgency(row.get("pain_point", "")),
                            "company_size": self._infer_company_size(
                                row.get("pain_point", "")
                            ),
                        }

                        documents.append(Document(text=doc_text, metadata=metadata))

            except Exception as e:
                print(f"⚠️ Error processing {metrics_file}: {e}")

        # Load from manual Reddit data if exists
        reddit_data_files = list(self.data_dir.glob("reddit_*.json"))

        for reddit_file in reddit_data_files:
            try:
                with open(reddit_file) as f:
                    reddit_data = json.load(f)

                for entry in reddit_data:
                    doc_text = self._format_reddit_json_document(entry)

                    metadata = {
                        "source": "reddit",
                        "data_type": "discussion",
                        "subreddit": entry.get("subreddit", ""),
                        "author": entry.get("author", ""),
                        "score": entry.get("score", 0),
                        "created_utc": entry.get("created_utc", ""),
                        "category": self._categorize_pain_point(entry.get("text", "")),
                        "sentiment": self._analyze_sentiment(entry.get("text", "")),
                    }

                    documents.append(Document(text=doc_text, metadata=metadata))

            except Exception as e:
                print(f"⚠️ Error processing {reddit_file}: {e}")

        print(f"✅ Reddit knowledge base built: {len(documents)} documents")
        return documents

    @performance_monitor
    async def build_market_trends_knowledge_base(self) -> list[Document]:
        """Build market trends knowledge base from SerpAPI and metrics data"""

        print("🔧 Building market trends knowledge base...")

        documents = []

        # Load from SerpAPI results if available
        serpapi_files = list(self.data_dir.glob("serpapi_*.json"))

        for serpapi_file in serpapi_files:
            try:
                with open(serpapi_file) as f:
                    serpapi_data = json.load(f)

                for result in serpapi_data.get("organic_results", []):
                    doc_text = self._format_serpapi_document(result)

                    metadata = {
                        "source": "serpapi",
                        "data_type": "search_result",
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "position": result.get("position", 0),
                        "snippet": result.get("snippet", ""),
                        "domain": self._extract_domain(result.get("link", "")),
                        "relevance_score": self._calculate_relevance_score(result),
                    }

                    documents.append(Document(text=doc_text, metadata=metadata))

            except Exception as e:
                print(f"⚠️ Error processing {serpapi_file}: {e}")

        # Load from daily metrics for trend analysis
        metrics_files = list(self.data_dir.glob("metrics-daily-*.csv"))

        for metrics_file in metrics_files:
            try:
                df = pd.read_csv(metrics_file)

                # Aggregate by date for trend analysis
                trend_summary = self._create_trend_summary(df)

                doc_text = self._format_trend_document(trend_summary, metrics_file.name)

                metadata = {
                    "source": "metrics",
                    "data_type": "trend_analysis",
                    "file": metrics_file.name,
                    "date_range": f"{df['date'].min()} to {df['date'].max()}",
                    "total_entries": len(df),
                    "trend_direction": trend_summary.get("direction", "stable"),
                    "growth_rate": trend_summary.get("growth_rate", 0),
                }

                documents.append(Document(text=doc_text, metadata=metadata))

            except Exception as e:
                print(f"⚠️ Error processing {metrics_file}: {e}")

        print(f"✅ Market trends knowledge base built: {len(documents)} documents")
        return documents

    @performance_monitor
    async def build_github_knowledge_base(self) -> list[Document]:
        """Build GitHub insights knowledge base from developer data"""

        print("🔧 Building GitHub insights knowledge base...")

        documents = []

        # Load from GitHub prospects database if exists
        github_files = [
            "github_prospects_database.json",
            "prospects_database.json",  # May contain GitHub data
        ]

        for github_file in github_files:
            github_path = Path(github_file)
            if github_path.exists():
                try:
                    with open(github_path) as f:
                        github_data = json.load(f)

                    for prospect in github_data:
                        if prospect.get("source") == "github_discovery":
                            doc_text = self._format_github_document(prospect)

                            metadata = {
                                "source": "github",
                                "data_type": "developer_profile",
                                "username": prospect.get("username", ""),
                                "company": prospect.get("company", ""),
                                "bio": prospect.get("bio", ""),
                                "location": prospect.get("location", ""),
                                "followers": prospect.get("followers", 0),
                                "repositories": prospect.get("repositories", 0),
                                "repo_language": prospect.get("repo_language", ""),
                                "prospect_score": prospect.get("prospect_score", 0),
                                "tech_stack": self._extract_tech_stack(prospect),
                                "experience_level": self._assess_experience_level(
                                    prospect
                                ),
                            }

                            documents.append(Document(text=doc_text, metadata=metadata))

                except Exception as e:
                    print(f"⚠️ Error processing {github_file}: {e}")

        # Load from repository analysis data if available
        repo_files = list(self.data_dir.glob("github_repos_*.json"))

        for repo_file in repo_files:
            try:
                with open(repo_file) as f:
                    repo_data = json.load(f)

                for repo in repo_data:
                    doc_text = self._format_repository_document(repo)

                    metadata = {
                        "source": "github",
                        "data_type": "repository",
                        "name": repo.get("name", ""),
                        "language": repo.get("language", ""),
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "description": repo.get("description", ""),
                        "topics": repo.get("topics", []),
                        "complexity": self._assess_repo_complexity(repo),
                        "business_potential": self._assess_business_potential(repo),
                    }

                    documents.append(Document(text=doc_text, metadata=metadata))

            except Exception as e:
                print(f"⚠️ Error processing {repo_file}: {e}")

        print(f"✅ GitHub knowledge base built: {len(documents)} documents")
        return documents

    @performance_monitor
    async def build_historical_reports_knowledge_base(self) -> list[Document]:
        """Build knowledge base from historical reports and insights"""

        print("🔧 Building historical reports knowledge base...")

        documents = []

        # Load daily insight reports
        insight_files = list(self.reports_dir.glob("insight_daily_*.md"))

        for insight_file in insight_files:
            try:
                with open(insight_file, encoding="utf-8") as f:
                    content = f.read()

                # Parse structured sections
                parsed_content = self._parse_insight_report(content)

                doc_text = self._format_insight_document(
                    parsed_content, insight_file.name
                )

                # Extract date from filename
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", insight_file.name)
                report_date = date_match.group(1) if date_match else ""

                metadata = {
                    "source": "historical_reports",
                    "data_type": "daily_insight",
                    "filename": insight_file.name,
                    "report_date": report_date,
                    "word_count": len(content.split()),
                    "pain_points_count": len(parsed_content.get("pain_points", [])),
                    "themes_count": len(parsed_content.get("themes", [])),
                    "opportunities_count": len(parsed_content.get("opportunities", [])),
                    "report_quality": self._assess_report_quality(parsed_content),
                }

                documents.append(Document(text=doc_text, metadata=metadata))

            except Exception as e:
                print(f"⚠️ Error processing {insight_file}: {e}")

        # Load weekly reports
        weekly_files = list(self.reports_dir.glob("weekly_*.md"))

        for weekly_file in weekly_files:
            try:
                with open(weekly_file, encoding="utf-8") as f:
                    content = f.read()

                doc_text = self._format_weekly_document(content, weekly_file.name)

                metadata = {
                    "source": "historical_reports",
                    "data_type": "weekly_summary",
                    "filename": weekly_file.name,
                    "word_count": len(content.split()),
                    "report_type": "weekly_analysis",
                }

                documents.append(Document(text=doc_text, metadata=metadata))

            except Exception as e:
                print(f"⚠️ Error processing {weekly_file}: {e}")

        print(f"✅ Historical reports knowledge base built: {len(documents)} documents")
        return documents

    def _format_reddit_document(self, row: pd.Series) -> str:
        """Format Reddit data into a structured document"""

        return f"""
**Reddit Pain Point Analysis**

**Pain Point:** {row.get('pain_point', 'N/A')}

**Context:**
- Subreddit: {row.get('subreddit', 'N/A')}
- Score: {row.get('score', 0)}
- Comments: {row.get('comment_count', 0)}
- Date: {row.get('date', 'N/A')}

**Analysis:**
This pain point was identified in r/{row.get('subreddit', 'unknown')} and received {row.get('score', 0)} upvotes with {row.get('comment_count', 0)} comments, indicating community engagement and validation.

**Business Implications:**
{self._generate_business_implications(row.get('pain_point', ''))}
        """.strip()

    def _format_reddit_json_document(self, entry: dict[str, Any]) -> str:
        """Format Reddit JSON data into a structured document"""

        return f"""
**Reddit Discussion Analysis**

**Title:** {entry.get('title', 'N/A')}

**Content:** {entry.get('text', 'N/A')}

**Metadata:**
- Author: {entry.get('author', 'N/A')}
- Subreddit: {entry.get('subreddit', 'N/A')}
- Score: {entry.get('score', 0)}
- Created: {entry.get('created_utc', 'N/A')}

**Key Insights:**
{self._extract_key_insights(entry.get('text', ''))}
        """.strip()

    def _format_serpapi_document(self, result: dict[str, Any]) -> str:
        """Format SerpAPI result into a structured document"""

        return f"""
**Search Result Analysis**

**Title:** {result.get('title', 'N/A')}

**Snippet:** {result.get('snippet', 'N/A')}

**Source:** {result.get('link', 'N/A')}

**Position:** {result.get('position', 'N/A')}

**Market Intelligence:**
This search result indicates market interest in related topics. The positioning and content suggest {self._analyze_market_signal(result)}.

**Competitive Landscape:**
Domain authority and content quality suggest {self._analyze_competition(result)}.
        """.strip()

    def _format_github_document(self, prospect: dict[str, Any]) -> str:
        """Format GitHub prospect into a structured document"""

        return f"""
**GitHub Developer Profile Analysis**

**Developer:** {prospect.get('name', 'N/A')} (@{prospect.get('username', 'N/A')})

**Company:** {prospect.get('company', 'N/A')}

**Bio:** {prospect.get('bio', 'N/A')}

**Technical Profile:**
- Followers: {prospect.get('followers', 0)}
- Public Repositories: {prospect.get('repositories', 0)}
- Primary Language: {prospect.get('repo_language', 'N/A')}
- Location: {prospect.get('location', 'N/A')}

**Recent Project:** {prospect.get('repo_name', 'N/A')}
**Project Description:** {prospect.get('repo_description', 'N/A')}
**Project Stars:** {prospect.get('repo_stars', 0)}

**Prospect Analysis:**
- Prospect Score: {prospect.get('prospect_score', 0)}/100
- Targeting Reasons: {', '.join(prospect.get('targeting_reasons', []))}

**Business Insights:**
{self._generate_developer_insights(prospect)}
        """.strip()

    def _format_insight_document(
        self, parsed_content: dict[str, Any], filename: str
    ) -> str:
        """Format parsed insight report into a structured document"""

        pain_points = "\n".join(
            [f"- {pp}" for pp in parsed_content.get("pain_points", [])]
        )
        themes = "\n".join([f"- {theme}" for theme in parsed_content.get("themes", [])])
        opportunities = "\n".join(
            [f"- {opp}" for opp in parsed_content.get("opportunities", [])]
        )

        return f"""
**Daily Market Intelligence Report**

**Report:** {filename}
**Date:** {parsed_content.get('date', 'N/A')}

**Executive Summary:**
{parsed_content.get('summary', 'N/A')}

**Key Pain Points Identified:**
{pain_points}

**Major Themes:**
{themes}

**Market Opportunities:**
{opportunities}

**Trend Analysis:**
{parsed_content.get('trend_analysis', 'N/A')}

**Strategic Recommendations:**
{parsed_content.get('recommendations', 'N/A')}
        """.strip()

    def _categorize_pain_point(self, pain_point: str) -> str:
        """Categorize pain point by type"""

        pain_point_lower = pain_point.lower()

        if any(
            word in pain_point_lower
            for word in ["integration", "api", "connect", "sync"]
        ):
            return "integration"
        elif any(
            word in pain_point_lower
            for word in ["automation", "manual", "automate", "workflow"]
        ):
            return "automation"
        elif any(
            word in pain_point_lower
            for word in ["data", "analytics", "reporting", "dashboard"]
        ):
            return "data_analytics"
        elif any(
            word in pain_point_lower
            for word in ["customer", "user", "client", "support"]
        ):
            return "customer_management"
        elif any(
            word in pain_point_lower
            for word in ["payment", "billing", "invoice", "pricing"]
        ):
            return "payments"
        elif any(
            word in pain_point_lower
            for word in ["security", "auth", "compliance", "gdpr"]
        ):
            return "security"
        else:
            return "general"

    def _assess_urgency(self, pain_point: str) -> str:
        """Assess urgency level of pain point"""

        pain_point_lower = pain_point.lower()

        if any(
            word in pain_point_lower
            for word in ["urgent", "critical", "breaking", "emergency", "asap"]
        ):
            return "high"
        elif any(
            word in pain_point_lower for word in ["need", "important", "soon", "help"]
        ):
            return "medium"
        else:
            return "low"

    def _infer_company_size(self, pain_point: str) -> str:
        """Infer company size from pain point context"""

        pain_point_lower = pain_point.lower()

        if any(
            word in pain_point_lower
            for word in ["startup", "founding", "early stage", "bootstrapped"]
        ):
            return "startup"
        elif any(
            word in pain_point_lower
            for word in ["team", "small business", "smb", "growing"]
        ):
            return "smb"
        elif any(
            word in pain_point_lower
            for word in ["enterprise", "large", "corporation", "scale"]
        ):
            return "enterprise"
        else:
            return "unknown"

    def _parse_insight_report(self, content: str) -> dict[str, Any]:
        """Parse structured insight report content"""

        parsed = {
            "pain_points": [],
            "themes": [],
            "opportunities": [],
            "summary": "",
            "date": "",
            "trend_analysis": "",
            "recommendations": "",
        }

        # Extract pain points
        pain_points_match = re.search(
            r"\*\*Recent Pain Points Identified:\*\*(.*?)(?=\*\*|$)", content, re.DOTALL
        )
        if pain_points_match:
            pain_points_text = pain_points_match.group(1)
            parsed["pain_points"] = re.findall(r"- \*\*(.*?)\*\*", pain_points_text)

        # Extract themes
        themes_match = re.search(
            r"## 🎯 Key Themes Analysis(.*?)(?=##|$)", content, re.DOTALL
        )
        if themes_match:
            themes_text = themes_match.group(1)
            parsed["themes"] = re.findall(r"### \d+\. (.*?)(?=\n|$)", themes_text)

        # Extract opportunities
        opportunities_match = re.search(
            r"## 💡 Underserved SaaS Niches(.*?)(?=##|$)", content, re.DOTALL
        )
        if opportunities_match:
            opportunities_text = opportunities_match.group(1)
            parsed["opportunities"] = re.findall(
                r"### \d+\. (.*?)(?=\n|$)", opportunities_text
            )

        return parsed

    def _generate_business_implications(self, pain_point: str) -> str:
        """Generate business implications for a pain point"""

        category = self._categorize_pain_point(pain_point)

        implications = {
            "integration": "API and integration solutions have high demand and recurring revenue potential.",
            "automation": "Workflow automation represents significant efficiency gains and cost savings.",
            "data_analytics": "Data visualization and analytics tools have strong product-market fit.",
            "customer_management": "CRM and customer support tools are essential for scaling businesses.",
            "payments": "Payment and billing solutions have transaction-based revenue models.",
            "security": "Security and compliance tools are mission-critical with high willingness to pay.",
        }

        return implications.get(
            category,
            "This represents a potential SaaS opportunity with market validation.",
        )

    def _extract_key_insights(self, text: str) -> str:
        """Extract key insights from text content"""

        # Simple keyword-based insight extraction
        keywords = [
            "problem",
            "issue",
            "challenge",
            "need",
            "want",
            "frustrat",
            "difficult",
        ]

        sentences = text.split(".")
        insights = []

        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                insights.append(sentence.strip())

        return (
            ". ".join(insights[:3])
            if insights
            else "General discussion about SaaS tools and workflows."
        )

    def _analyze_market_signal(self, result: dict[str, Any]) -> str:
        """Analyze market signal from search result"""

        position = result.get("position", 0)
        title = result.get("title", "").lower()

        if position <= 3:
            return "strong market demand and high competition"
        elif "review" in title or "comparison" in title:
            return "active evaluation and purchasing behavior"
        elif "tutorial" in title or "how to" in title:
            return "educational need and potential solution gaps"
        else:
            return "moderate market interest"

    def _analyze_competition(self, result: dict[str, Any]) -> str:
        """Analyze competition from search result"""

        link = result.get("link", "")

        if any(
            domain in link
            for domain in ["capterra.com", "g2.com", "softwareadvice.com"]
        ):
            return "established marketplace presence with multiple competitors"
        elif any(domain in link for domain in ["github.com", "stackoverflow.com"]):
            return "technical solutions with open source alternatives"
        elif ".com" in link and "blog" not in link:
            return "direct commercial competition"
        else:
            return "mixed competitive landscape"

    def _generate_developer_insights(self, prospect: dict[str, Any]) -> str:
        """Generate business insights for developer prospect"""

        score = prospect.get("prospect_score", 0)
        language = prospect.get("repo_language", "")
        company = prospect.get("company", "")

        insights = []

        if score >= 70:
            insights.append("High-value prospect with strong technical credibility.")

        if language:
            insights.append(
                f"{language} expertise suggests specific tooling needs and integration requirements."
            )

        if "founder" in company.lower() or "ceo" in company.lower():
            insights.append(
                "Decision-maker with budget authority and strategic vision."
            )

        return (
            " ".join(insights)
            if insights
            else "Potential technical influencer in SaaS space."
        )

    def _create_trend_summary(self, df: pd.DataFrame) -> dict[str, Any]:
        """Create trend summary from metrics data"""

        # Simple trend analysis
        if "score" in df.columns and len(df) > 1:
            scores = df["score"].tolist()
            growth_rate = (scores[-1] - scores[0]) / scores[0] if scores[0] != 0 else 0
            direction = (
                "growing"
                if growth_rate > 0.1
                else "declining" if growth_rate < -0.1 else "stable"
            )
        else:
            growth_rate = 0
            direction = "stable"

        return {
            "direction": direction,
            "growth_rate": growth_rate,
            "total_entries": len(df),
            "date_range": (
                f"{df['date'].min()} to {df['date'].max()}"
                if "date" in df.columns
                else "unknown"
            ),
        }

    def _format_trend_document(
        self, trend_summary: dict[str, Any], filename: str
    ) -> str:
        """Format trend summary into document"""

        return f"""
**Market Trend Analysis**

**Source:** {filename}
**Date Range:** {trend_summary.get('date_range', 'N/A')}
**Total Data Points:** {trend_summary.get('total_entries', 0)}

**Trend Direction:** {trend_summary.get('direction', 'stable')}
**Growth Rate:** {trend_summary.get('growth_rate', 0):.2%}

**Analysis:**
The data shows a {trend_summary.get('direction', 'stable')} trend over the analyzed period.
This indicates {self._interpret_trend(trend_summary)} market conditions.

**Strategic Implications:**
{self._generate_trend_implications(trend_summary)}
        """.strip()

    def _interpret_trend(self, trend_summary: dict[str, Any]) -> str:
        """Interpret trend direction"""

        direction = trend_summary.get("direction", "stable")

        if direction == "growing":
            return "expanding market demand and increasing opportunity"
        elif direction == "declining":
            return "contracting market or increased competition"
        else:
            return "stable market conditions with consistent demand"

    def _generate_trend_implications(self, trend_summary: dict[str, Any]) -> str:
        """Generate strategic implications from trend"""

        direction = trend_summary.get("direction", "stable")
        growth_rate = trend_summary.get("growth_rate", 0)

        if direction == "growing" and growth_rate > 0.2:
            return "High-growth opportunity with strong market momentum. Consider accelerated investment."
        elif direction == "growing":
            return "Positive market trend with moderate growth potential. Monitor for acceleration."
        elif direction == "declining":
            return "Market contraction or saturation. Investigate causes and consider pivot opportunities."
        else:
            return "Stable market with consistent demand. Focus on differentiation and efficiency."

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""

        import urllib.parse

        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc
        except Exception:
            return "unknown"

    def _calculate_relevance_score(self, result: dict[str, Any]) -> float:
        """Calculate relevance score for search result"""

        position = result.get("position", 10)
        title = result.get("title", "")
        snippet = result.get("snippet", "")

        # Simple scoring based on position and keyword relevance
        position_score = max(0, (10 - position) / 10)

        # Keyword relevance
        keywords = ["saas", "software", "platform", "automation", "tool"]
        text = f"{title} {snippet}".lower()
        keyword_score = sum(1 for keyword in keywords if keyword in text) / len(
            keywords
        )

        return (position_score + keyword_score) / 2

    def _extract_tech_stack(self, prospect: dict[str, Any]) -> str:
        """Extract technology stack from prospect data"""

        language = prospect.get("repo_language", "")
        repo_desc = prospect.get("repo_description", "").lower()

        tech_indicators = {
            "python": ["python", "django", "flask", "fastapi"],
            "javascript": ["javascript", "react", "node", "vue", "angular"],
            "go": ["go", "golang"],
            "rust": ["rust"],
            "java": ["java", "spring"],
            "typescript": ["typescript", "ts"],
        }

        stack = [language] if language else []

        for tech, indicators in tech_indicators.items():
            if any(indicator in repo_desc for indicator in indicators):
                if tech not in stack:
                    stack.append(tech)

        return ", ".join(stack) if stack else "unknown"

    def _assess_experience_level(self, prospect: dict[str, Any]) -> str:
        """Assess developer experience level"""

        followers = prospect.get("followers", 0)
        repositories = prospect.get("repositories", 0)
        score = prospect.get("prospect_score", 0)

        if followers > 100 and repositories > 20 and score > 80:
            return "senior"
        elif followers > 50 and repositories > 10:
            return "intermediate"
        else:
            return "junior"

    def _assess_repo_complexity(self, repo: dict[str, Any]) -> str:
        """Assess repository complexity"""

        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        description = repo.get("description", "").lower()

        if stars > 100 and forks > 20:
            return "high"
        elif stars > 10 and ("framework" in description or "library" in description):
            return "medium"
        else:
            return "low"

    def _assess_business_potential(self, repo: dict[str, Any]) -> str:
        """Assess business potential of repository"""

        description = repo.get("description", "").lower()
        topics = repo.get("topics", [])

        business_keywords = [
            "saas",
            "platform",
            "tool",
            "automation",
            "api",
            "dashboard",
        ]

        if any(keyword in description for keyword in business_keywords):
            return "high"
        elif any(topic in topics for topic in ["business", "saas", "automation"]):
            return "medium"
        else:
            return "low"

    def _assess_report_quality(self, parsed_content: dict[str, Any]) -> str:
        """Assess quality of insight report"""

        pain_points = len(parsed_content.get("pain_points", []))
        themes = len(parsed_content.get("themes", []))
        opportunities = len(parsed_content.get("opportunities", []))

        total_insights = pain_points + themes + opportunities

        if total_insights >= 15:
            return "high"
        elif total_insights >= 8:
            return "medium"
        else:
            return "low"

    def _format_weekly_document(self, content: str, filename: str) -> str:
        """Format weekly report into structured document"""

        return f"""
**Weekly Market Intelligence Summary**

**Report:** {filename}

**Content:**
{content[:2000]}...

**Analysis Type:** Weekly aggregation and trend analysis
**Scope:** Multi-day market intelligence synthesis
**Format:** Comprehensive strategic overview
        """.strip()

    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""

        positive_words = ["good", "great", "excellent", "love", "amazing", "perfect"]
        negative_words = [
            "bad",
            "terrible",
            "hate",
            "awful",
            "frustrat",
            "problem",
            "issue",
        ]

        text_lower = text.lower()

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"


async def main():
    """Test the knowledge base builder"""

    print("🧪 Testing Knowledge Base Builder")

    builder = KnowledgeBaseBuilder()

    # Test Reddit knowledge base
    reddit_docs = await builder.build_reddit_knowledge_base()
    print(f"Reddit documents: {len(reddit_docs)}")

    # Test market trends knowledge base
    trends_docs = await builder.build_market_trends_knowledge_base()
    print(f"Market trends documents: {len(trends_docs)}")

    # Test GitHub knowledge base
    github_docs = await builder.build_github_knowledge_base()
    print(f"GitHub documents: {len(github_docs)}")

    # Test historical reports knowledge base
    reports_docs = await builder.build_historical_reports_knowledge_base()
    print(f"Historical reports documents: {len(reports_docs)}")

    print("✅ Knowledge base building test complete")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
