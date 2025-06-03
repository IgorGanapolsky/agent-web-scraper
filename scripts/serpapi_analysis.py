#!/usr/bin/env python3
"""
SerpAPI-Based Niche Scoring Module
Analyzes keyword/niche opportunities using SerpAPI search results
"""

import os
import re
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv
from serpapi.google_search import GoogleSearch

load_dotenv()


class SerpAPINicheAnalyzer:
    def __init__(self):
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        if not self.serpapi_key:
            print("⚠️  SERPAPI_KEY not found, using mock data")
            self.use_mock_data = True
        else:
            self.use_mock_data = False

    def analyze_keyword(self, keyword: str, num_results: int = 10) -> dict[str, Any]:
        """
        Analyze a keyword/niche for market opportunity using SerpAPI

        Args:
            keyword: The keyword or niche to analyze
            num_results: Number of search results to analyze

        Returns:
            Dictionary with analysis results including domains, classifications, and score
        """
        if self.use_mock_data:
            return self._generate_mock_analysis(keyword)

        try:
            # Configure search parameters
            search_params = {
                "q": keyword,
                "api_key": self.serpapi_key,
                "num": num_results,
                "gl": "us",
                "hl": "en",
            }

            # Perform the search
            search = GoogleSearch(search_params)
            results = search.get_dict()

            # Extract organic results
            organic_results = results.get("organic_results", [])

            if not organic_results:
                return self._generate_empty_analysis(keyword)

            # Analyze the results
            analysis = self._analyze_serp_results(keyword, organic_results)

            return analysis

        except Exception as e:
            print(f"❌ Error analyzing keyword '{keyword}': {e}")
            return self._generate_mock_analysis(keyword)

    def _analyze_serp_results(
        self, keyword: str, organic_results: list[dict]
    ) -> dict[str, Any]:
        """Analyze SERP results and classify domains"""
        domains = []
        saas_competitors = []
        review_sites = []
        blog_results = []
        authority_sites = []

        # Known domain classifications
        saas_domains = {
            "salesforce.com",
            "hubspot.com",
            "slack.com",
            "notion.so",
            "airtable.com",
            "zapier.com",
            "mailchimp.com",
            "stripe.com",
            "intercom.com",
            "zendesk.com",
            "asana.com",
            "trello.com",
            "monday.com",
            "clickup.com",
            "pipedrive.com",
            "convertkit.com",
            "mixpanel.com",
            "amplitude.com",
            "hotjar.com",
            "chargebee.com",
            "recurly.com",
            "chargify.com",
            "zuora.com",
        }

        review_domains = {
            "g2.com",
            "capterra.com",
            "trustpilot.com",
            "softwareadvice.com",
            "getapp.com",
            "sourceforge.net",
            "alternativeto.net",
        }

        authority_domains = {
            "forbes.com",
            "techcrunch.com",
            "entrepreneur.com",
            "inc.com",
            "fastcompany.com",
            "harvard.edu",
            "mit.edu",
            "wikipedia.org",
            "medium.com",
            "linkedin.com",
        }

        for result in organic_results:
            link = result.get("link", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            if not link:
                continue

            try:
                domain = urlparse(link).netloc.lower()
                # Remove www. prefix
                domain = re.sub(r"^www\.", "", domain)

                domains.append(
                    {"domain": domain, "title": title, "snippet": snippet, "link": link}
                )

                # Classify domain
                if any(saas_domain in domain for saas_domain in saas_domains):
                    saas_competitors.append(domain)
                elif any(review_domain in domain for review_domain in review_domains):
                    review_sites.append(domain)
                elif any(auth_domain in domain for auth_domain in authority_domains):
                    authority_sites.append(domain)
                elif self._is_blog_domain(domain, title, snippet):
                    blog_results.append(domain)
                elif self._looks_like_saas(domain, title, snippet):
                    saas_competitors.append(domain)

            except Exception as e:
                print(f"Error processing result: {e}")
                continue

        # Calculate niche opportunity score
        niche_score = self._calculate_niche_score(
            saas_competitors, review_sites, blog_results, authority_sites
        )

        return {
            "keyword": keyword,
            "total_results": len(domains),
            "domains": domains,
            "saas_competitors": saas_competitors,
            "review_sites": review_sites,
            "blog_results": blog_results,
            "authority_sites": authority_sites,
            "niche_score": niche_score,
            "opportunity_level": self._get_opportunity_level(niche_score),
            "top_domains": [d["domain"] for d in domains[:5]],
        }

    def _is_blog_domain(self, domain: str, title: str, snippet: str) -> bool:
        """Check if domain appears to be a blog"""
        blog_indicators = ["blog", "medium.com", "wordpress", "ghost.io", "substack"]
        content_indicators = ["how to", "guide", "tutorial", "best practices"]

        domain_is_blog = any(
            indicator in domain.lower() for indicator in blog_indicators
        )
        content_is_blog = any(
            indicator in (title + snippet).lower() for indicator in content_indicators
        )

        return domain_is_blog or content_is_blog

    def _looks_like_saas(self, domain: str, title: str, snippet: str) -> bool:
        """Check if domain/content looks like a SaaS product"""
        saas_indicators = [
            "software",
            "platform",
            "tool",
            "app",
            "service",
            "solution",
            "dashboard",
            "analytics",
            "automation",
            "management",
            "api",
        ]

        content = (domain + title + snippet).lower()
        return any(indicator in content for indicator in saas_indicators)

    def _calculate_niche_score(
        self,
        saas_competitors: list[str],
        review_sites: list[str],
        blog_results: list[str],
        authority_sites: list[str],
    ) -> float:
        """Calculate niche opportunity score (0-10 scale)"""
        num_saas = len(saas_competitors)
        num_reviews = len(review_sites)
        num_blogs = len(blog_results)
        num_authority = len(authority_sites)

        # Base score starts at 10 (high opportunity)
        score = 10.0

        # Reduce score based on competition
        # Heavy penalty for many SaaS competitors
        score -= num_saas * 1.5

        # Medium penalty for authority sites
        score -= num_authority * 1.0

        # Light penalty for review sites (indicates established market)
        score -= num_reviews * 0.5

        # Slight boost for blog content (indicates interest but less competition)
        score += min(num_blogs * 0.2, 1.0)

        # Ensure score is between 0 and 10
        return max(0.0, min(10.0, score))

    def _get_opportunity_level(self, score: float) -> str:
        """Convert numeric score to opportunity level"""
        if score >= 7.0:
            return "🔥 High"
        elif score >= 4.0:
            return "⚠️ Moderate"
        else:
            return "🧱 Crowded"

    def _generate_mock_analysis(self, keyword: str) -> dict[str, Any]:
        """Generate mock analysis for testing"""
        import random

        mock_domains = [
            "example-saas.com",
            "competitor-tool.io",
            "blog-about-topic.com",
            "authority-site.com",
            "review-platform.com",
        ]

        # Simulate varying competition levels
        num_saas = random.randint(1, 8)
        num_reviews = random.randint(0, 3)
        num_blogs = random.randint(2, 6)

        saas_competitors = mock_domains[:num_saas]
        review_sites = ["g2.com", "capterra.com"][:num_reviews]
        blog_results = [f"blog-{i}.com" for i in range(num_blogs)]

        score = self._calculate_niche_score(
            saas_competitors, review_sites, blog_results, []
        )

        return {
            "keyword": keyword,
            "total_results": 10,
            "domains": [
                {
                    "domain": d,
                    "title": f"Title for {d}",
                    "snippet": f"Snippet for {d}",
                    "link": f"https://{d}",
                }
                for d in mock_domains
            ],
            "saas_competitors": saas_competitors,
            "review_sites": review_sites,
            "blog_results": blog_results,
            "authority_sites": [],
            "niche_score": score,
            "opportunity_level": self._get_opportunity_level(score),
            "top_domains": mock_domains[:5],
        }

    def _generate_empty_analysis(self, keyword: str) -> dict[str, Any]:
        """Generate empty analysis when no results found"""
        return {
            "keyword": keyword,
            "total_results": 0,
            "domains": [],
            "saas_competitors": [],
            "review_sites": [],
            "blog_results": [],
            "authority_sites": [],
            "niche_score": 10.0,  # High opportunity if no results
            "opportunity_level": "🔥 High",
            "top_domains": [],
        }

    def analyze_multiple_keywords(self, keywords: list[str]) -> list[dict[str, Any]]:
        """Analyze multiple keywords and return sorted by opportunity score"""
        results = []

        for keyword in keywords:
            print(f"🔍 Analyzing keyword: {keyword}")
            analysis = self.analyze_keyword(keyword)
            results.append(analysis)

        # Sort by niche score (highest opportunity first)
        results.sort(key=lambda x: x["niche_score"], reverse=True)

        return results


def main():
    """Test the analyzer with sample keywords"""
    analyzer = SerpAPINicheAnalyzer()

    test_keywords = [
        "ai onboarding automation",
        "subscription billing saas",
        "b2b lead scoring tools",
        "customer success platforms",
    ]

    print("🚀 Testing SerpAPI Niche Analyzer...")

    results = analyzer.analyze_multiple_keywords(test_keywords)

    print("\n📊 Results Summary:")
    for result in results:
        keyword = result["keyword"]
        score = result["niche_score"]
        level = result["opportunity_level"]
        competitors = len(result["saas_competitors"])

        print(
            f"• {keyword}: {level} (Score: {score:.1f}, {competitors} SaaS competitors)"
        )


if __name__ == "__main__":
    main()
