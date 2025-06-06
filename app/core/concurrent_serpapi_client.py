"""
Concurrent SerpAPI Client for Real-Time Market Intelligence
Optimized for CMO market analysis and CFO competitive pricing research.
"""

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

from app.config.logging import get_logger
from app.core.batch_api_optimizer import get_batch_optimizer

load_dotenv()

logger = get_logger(__name__)


@dataclass
class SerpSearchTask:
    """Individual search task for concurrent processing"""

    query: str
    location: str = "United States"
    device: str = "desktop"
    hl: str = "en"
    gl: str = "us"
    num_results: int = 10
    task_type: str = (
        "market_research"  # market_research, competitor_pricing, trend_analysis
    )
    metadata: Optional[dict[str, Any]] = None


class ConcurrentSerpAPIClient:
    """
    Enterprise SerpAPI client with concurrent processing capabilities.
    Optimized for real-time market intelligence and competitive analysis.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpAPI client with concurrent processing support.

        Args:
            api_key: SerpAPI key. Falls back to SERPAPI_API_KEY env var
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY environment variable not set")

        self.base_url = "https://serpapi.com/search"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.batch_optimizer = get_batch_optimizer()

    async def concurrent_market_research(
        self, search_queries: list[str], location: str = "United States"
    ) -> dict[str, Any]:
        """
        Execute multiple market research queries concurrently.
        Perfect for CMO market trend analysis.

        Args:
            search_queries: List of search terms for market analysis
            location: Geographic location for results

        Returns:
            Comprehensive market intelligence report
        """
        start_time = time.time()

        # Create concurrent search tasks
        search_tasks = [
            SerpSearchTask(
                query=query,
                location=location,
                task_type="market_research",
                metadata={"priority": "high" if i == 0 else "normal"},
            )
            for i, query in enumerate(search_queries)
        ]

        logger.info(
            f"Starting concurrent market research for {len(search_tasks)} queries"
        )

        # Execute searches concurrently
        search_results = await self._execute_concurrent_searches(search_tasks)

        # Process results for market insights
        market_intelligence = await self._analyze_market_data(search_results)

        execution_time = time.time() - start_time

        return {
            "market_intelligence": market_intelligence,
            "raw_search_results": search_results,
            "performance_metrics": {
                "total_queries": len(search_queries),
                "execution_time": execution_time,
                "queries_per_second": len(search_queries) / execution_time,
                "optimization_method": "concurrent_api_calls",
            },
        }

    async def concurrent_competitor_pricing(
        self, competitor_brands: list[str], product_category: str
    ) -> dict[str, Any]:
        """
        Analyze competitor pricing across multiple brands concurrently.
        Critical for CFO pricing strategy decisions.

        Args:
            competitor_brands: List of competitor brand names
            product_category: Product category for price comparison

        Returns:
            Competitive pricing analysis with recommendations
        """
        # Generate pricing-focused search queries
        pricing_queries = [
            f"{brand} {product_category} pricing cost price"
            for brand in competitor_brands
        ]

        # Add general market pricing queries
        pricing_queries.extend(
            [
                f"{product_category} market pricing trends 2025",
                f"{product_category} pricing comparison review",
                f"best {product_category} price value cost",
            ]
        )

        search_tasks = [
            SerpSearchTask(
                query=query,
                task_type="competitor_pricing",
                num_results=15,  # More results for pricing data
                metadata={
                    "brand": (
                        competitor_brands[i] if i < len(competitor_brands) else "market"
                    )
                },
            )
            for i, query in enumerate(pricing_queries)
        ]

        logger.info(f"Analyzing competitor pricing for {len(competitor_brands)} brands")

        # Execute pricing searches concurrently
        pricing_results = await self._execute_concurrent_searches(search_tasks)

        # Extract pricing intelligence
        pricing_analysis = await self._analyze_pricing_data(
            pricing_results, competitor_brands
        )

        return {
            "pricing_analysis": pricing_analysis,
            "competitor_data": pricing_results,
            "strategic_recommendations": await self._generate_pricing_strategy(
                pricing_analysis
            ),
        }

    async def real_time_trend_monitoring(
        self, trend_keywords: list[str], time_range: str = "past_week"
    ) -> dict[str, Any]:
        """
        Monitor emerging trends in real-time across multiple keywords.
        Essential for proactive market positioning.

        Args:
            trend_keywords: Keywords to monitor for trending topics
            time_range: Time range for trend analysis

        Returns:
            Real-time trend analysis with emerging opportunities
        """
        # Create trend-focused queries
        trend_queries = []
        for keyword in trend_keywords:
            trend_queries.extend(
                [
                    f"{keyword} trends 2025 emerging new",
                    f"{keyword} market growth forecast",
                    f"{keyword} news updates latest",
                    f"{keyword} startup companies funding",
                ]
            )

        search_tasks = [
            SerpSearchTask(
                query=query,
                task_type="trend_analysis",
                metadata={"keyword": keyword, "time_range": time_range},
            )
            for query in trend_queries
            for keyword in trend_keywords
            if keyword in query
        ]

        # Execute trend searches with high concurrency
        trend_results = await self._execute_concurrent_searches(
            search_tasks, max_concurrent=20
        )

        # Analyze trending patterns
        trend_analysis = await self._analyze_trend_patterns(
            trend_results, trend_keywords
        )

        return {
            "trending_opportunities": trend_analysis,
            "emerging_threats": await self._identify_market_threats(trend_results),
            "actionable_insights": await self._generate_trend_actions(trend_analysis),
        }

    async def _execute_concurrent_searches(
        self, search_tasks: list[SerpSearchTask], max_concurrent: int = 10
    ) -> list[dict[str, Any]]:
        """Execute multiple SerpAPI searches concurrently with rate limiting"""

        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single_search(task: SerpSearchTask) -> dict[str, Any]:
            async with semaphore:
                try:
                    params = {
                        "api_key": self.api_key,
                        "engine": "google",
                        "q": task.query,
                        "location": task.location,
                        "hl": task.hl,
                        "gl": task.gl,
                        "device": task.device,
                        "num": task.num_results,
                    }

                    response = await self.client.get(self.base_url, params=params)
                    response.raise_for_status()

                    result_data = response.json()

                    return {
                        "success": True,
                        "query": task.query,
                        "task_type": task.task_type,
                        "data": result_data,
                        "metadata": task.metadata,
                    }

                except Exception as e:
                    logger.error(f"SerpAPI search failed for '{task.query}': {e}")
                    return {
                        "success": False,
                        "query": task.query,
                        "task_type": task.task_type,
                        "error": str(e),
                        "metadata": task.metadata,
                    }

        # Execute all searches concurrently
        tasks = [execute_single_search(task) for task in search_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        successful_results = [
            result
            for result in results
            if isinstance(result, dict) and result.get("success", False)
        ]

        logger.info(
            f"Completed {len(successful_results)}/{len(search_tasks)} searches successfully"
        )

        return successful_results

    async def _analyze_market_data(
        self, search_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze search results for market intelligence insights"""

        organic_results = []
        news_results = []
        related_searches = []

        for result in search_results:
            if not result.get("success"):
                continue

            data = result.get("data", {})
            organic_results.extend(data.get("organic_results", []))
            news_results.extend(data.get("news_results", []))
            related_searches.extend(data.get("related_searches", []))

        return {
            "total_organic_results": len(organic_results),
            "total_news_mentions": len(news_results),
            "trending_keywords": [rs.get("query", "") for rs in related_searches[:10]],
            "top_domains": self._extract_top_domains(organic_results),
            "content_themes": self._extract_content_themes(organic_results),
            "market_sentiment": self._analyze_sentiment_indicators(
                organic_results + news_results
            ),
        }

    async def _analyze_pricing_data(
        self, pricing_results: list[dict[str, Any]], competitor_brands: list[str]
    ) -> dict[str, Any]:
        """Extract and analyze pricing intelligence from search results"""

        pricing_mentions = []
        for result in pricing_results:
            if not result.get("success"):
                continue

            organic_results = result.get("data", {}).get("organic_results", [])
            for item in organic_results:
                title = item.get("title", "").lower()
                snippet = item.get("snippet", "").lower()

                # Look for pricing indicators
                pricing_keywords = [
                    "price",
                    "cost",
                    "pricing",
                    "$",
                    "subscription",
                    "plan",
                    "fee",
                ]
                if any(keyword in title + snippet for keyword in pricing_keywords):
                    pricing_mentions.append(
                        {
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "link": item.get("link", ""),
                            "brand": self._identify_brand(item, competitor_brands),
                        }
                    )

        return {
            "pricing_mentions_found": len(pricing_mentions),
            "competitor_pricing_data": pricing_mentions,
            "pricing_keywords_detected": self._extract_pricing_keywords(
                pricing_mentions
            ),
            "brand_coverage": {
                brand: sum(1 for pm in pricing_mentions if pm["brand"] == brand)
                for brand in competitor_brands
            },
        }

    async def _analyze_trend_patterns(
        self, trend_results: list[dict[str, Any]], trend_keywords: list[str]
    ) -> dict[str, Any]:
        """Identify trending patterns and emerging opportunities"""

        trending_indicators = {
            "growth_signals": [],
            "emerging_technologies": [],
            "market_shifts": [],
            "competitive_movements": [],
        }

        for result in trend_results:
            if not result.get("success"):
                continue

            data = result.get("data", {})

            # Analyze news results for trend signals
            for news_item in data.get("news_results", []):
                title = news_item.get("title", "").lower()

                if any(
                    signal in title
                    for signal in ["growth", "increase", "rising", "trending"]
                ):
                    trending_indicators["growth_signals"].append(news_item)
                elif any(
                    tech in title for tech in ["ai", "automation", "platform", "saas"]
                ):
                    trending_indicators["emerging_technologies"].append(news_item)

        return trending_indicators

    def _extract_top_domains(
        self, organic_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Extract and rank top domains from search results"""
        domain_counts = {}

        for result in organic_results:
            link = result.get("link", "")
            if link:
                domain = link.split("/")[2] if len(link.split("/")) > 2 else link
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Sort by frequency and return top 10
        top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        return [{"domain": domain, "mentions": count} for domain, count in top_domains]

    def _extract_content_themes(
        self, organic_results: list[dict[str, Any]]
    ) -> list[str]:
        """Extract common themes from search result content"""
        # Simple keyword extraction - in production, use NLP
        all_text = " ".join(
            [
                result.get("title", "") + " " + result.get("snippet", "")
                for result in organic_results
            ]
        ).lower()

        # Common business themes
        theme_keywords = {
            "automation": ["automation", "automate", "automated"],
            "efficiency": ["efficiency", "optimize", "streamline"],
            "cost_reduction": ["cost", "save", "reduce", "budget"],
            "growth": ["growth", "scale", "expand", "increase"],
            "digital_transformation": ["digital", "transformation", "modernize"],
        }

        detected_themes = []
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                detected_themes.append(theme)

        return detected_themes

    def _analyze_sentiment_indicators(
        self, results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze sentiment indicators in search results"""
        positive_keywords = [
            "best",
            "top",
            "excellent",
            "great",
            "leading",
            "innovative",
        ]
        negative_keywords = [
            "problem",
            "issue",
            "difficult",
            "expensive",
            "slow",
            "poor",
        ]

        positive_count = 0
        negative_count = 0
        total_count = 0

        for result in results:
            text = (result.get("title", "") + " " + result.get("snippet", "")).lower()
            total_count += 1

            if any(keyword in text for keyword in positive_keywords):
                positive_count += 1
            if any(keyword in text for keyword in negative_keywords):
                negative_count += 1

        return {
            "sentiment_score": (positive_count - negative_count) / max(total_count, 1),
            "positive_mentions": positive_count,
            "negative_mentions": negative_count,
            "total_analyzed": total_count,
        }

    def _identify_brand(
        self, search_item: dict[str, Any], competitor_brands: list[str]
    ) -> str:
        """Identify which competitor brand a search result relates to"""
        text = (
            search_item.get("title", "") + " " + search_item.get("snippet", "")
        ).lower()

        for brand in competitor_brands:
            if brand.lower() in text:
                return brand

        return "unknown"

    def _extract_pricing_keywords(
        self, pricing_mentions: list[dict[str, Any]]
    ) -> list[str]:
        """Extract pricing-related keywords from mentions"""
        pricing_text = " ".join(
            [
                pm.get("title", "") + " " + pm.get("snippet", "")
                for pm in pricing_mentions
            ]
        ).lower()

        # Extract common pricing terms
        pricing_terms = [
            "subscription",
            "monthly",
            "annual",
            "plan",
            "tier",
            "package",
            "free",
            "premium",
        ]
        found_terms = [term for term in pricing_terms if term in pricing_text]

        return found_terms

    async def _generate_pricing_strategy(
        self, pricing_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate strategic pricing recommendations based on competitive analysis"""
        return {
            "recommended_positioning": "value-based pricing with competitive monitoring",
            "price_range_suggestion": "Analyze competitor pricing mentions for specific recommendations",
            "differentiation_opportunities": [
                "Bundle additional value-added services",
                "Offer transparent pricing vs competitors",
                "Provide flexible pricing tiers",
            ],
            "monitoring_recommendations": [
                "Set up automated competitor price tracking",
                "Monitor pricing mention sentiment",
                "Track competitor pricing changes monthly",
            ],
        }

    async def _identify_market_threats(
        self, trend_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Identify potential market threats from trend analysis"""
        threat_indicators = []

        threat_keywords = [
            "disruption",
            "threat",
            "challenge",
            "regulation",
            "ban",
            "restrict",
        ]

        for result in trend_results:
            if not result.get("success"):
                continue

            for news_item in result.get("data", {}).get("news_results", []):
                title = news_item.get("title", "").lower()
                if any(keyword in title for keyword in threat_keywords):
                    threat_indicators.append(
                        {
                            "title": news_item.get("title", ""),
                            "source": news_item.get("source", ""),
                            "threat_type": (
                                "regulatory"
                                if any(reg in title for reg in ["regulation", "ban"])
                                else "competitive"
                            ),
                        }
                    )

        return threat_indicators[:5]  # Top 5 threats

    async def _generate_trend_actions(
        self, trend_analysis: dict[str, Any]
    ) -> list[str]:
        """Generate actionable insights from trend analysis"""
        actions = []

        if trend_analysis.get("growth_signals"):
            actions.append(
                "Capitalize on growth trends by expanding in high-growth segments"
            )

        if trend_analysis.get("emerging_technologies"):
            actions.append(
                "Evaluate emerging technologies for product integration opportunities"
            )

        if trend_analysis.get("competitive_movements"):
            actions.append(
                "Monitor competitor strategies and prepare defensive/offensive responses"
            )

        if not actions:
            actions.append("Continue monitoring trends for emerging opportunities")

        return actions

    async def close(self):
        """Clean up resources"""
        await self.client.aclose()


# Global client instance
_serpapi_client = None


def get_concurrent_serpapi_client() -> ConcurrentSerpAPIClient:
    """Get the global concurrent SerpAPI client"""
    global _serpapi_client
    if _serpapi_client is None:
        _serpapi_client = ConcurrentSerpAPIClient()
    return _serpapi_client


# Convenience functions for common executive use cases
async def cmo_market_intelligence(
    market_keywords: list[str], competitor_brands: list[str] = None
) -> dict[str, Any]:
    """
    Comprehensive market intelligence for CMO decision-making.
    Combines market research and competitive analysis.
    """
    client = get_concurrent_serpapi_client()

    # Concurrent market and competitive analysis
    market_task = client.concurrent_market_research(market_keywords)

    competitive_task = None
    if competitor_brands:
        competitive_task = client.concurrent_competitor_pricing(
            competitor_brands, "SaaS platform"
        )

    # Execute concurrently
    if competitive_task:
        market_results, competitive_results = await asyncio.gather(
            market_task, competitive_task
        )

        return {
            "market_intelligence": market_results,
            "competitive_analysis": competitive_results,
            "strategic_summary": {
                "total_data_points": (
                    market_results["performance_metrics"]["total_queries"]
                    + len(competitive_results.get("competitor_data", []))
                ),
                "processing_efficiency": "Concurrent API optimization enabled",
            },
        }
    else:
        market_results = await market_task
        return {"market_intelligence": market_results}


async def cfo_pricing_intelligence(
    competitor_brands: list[str],
    product_category: str = "business intelligence platform",
) -> dict[str, Any]:
    """
    Focused pricing analysis for CFO strategic pricing decisions.
    """
    client = get_concurrent_serpapi_client()

    pricing_analysis = await client.concurrent_competitor_pricing(
        competitor_brands, product_category
    )

    return {
        "executive_summary": {
            "competitor_coverage": len(competitor_brands),
            "pricing_data_points": pricing_analysis["pricing_analysis"][
                "pricing_mentions_found"
            ],
            "strategic_recommendations": pricing_analysis["strategic_recommendations"],
        },
        "detailed_analysis": pricing_analysis,
    }
